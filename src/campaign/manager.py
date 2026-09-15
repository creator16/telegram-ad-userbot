import asyncio

from hydrogram.errors import FloodWait


TERMINAL_STATUSES = {
    "COMPLETED",
    "CANCELLED",
    "FAILED",
}

RESTARTABLE_STATUSES = {
    "READY",
    "STOPPED",
    "RUNNING",
    "ROUND_WAIT",
}


class CampaignManager:

    def __init__(self, app, db):
        self.app = app
        self.db = db

        self.task = None
        self.paused = False
        self.stop_requested = False

    @property
    def running(self) -> bool:
        return (
            self.task is not None
            and not self.task.done()
        )

    async def start(self):

        if self.running:
            return False, "Campaign is already running."

        campaign = self.db.get_latest_campaign()

        if campaign is None:
            return False, "No campaign exists."

        status = campaign["status"]

        if status in TERMINAL_STATUSES:
            return (
                False,
                (
                    f"Campaign #{campaign['id']} "
                    f"is {status} and cannot be restarted."
                ),
            )

        if status not in RESTARTABLE_STATUSES:
            return (
                False,
                (
                    f"Campaign #{campaign['id']} "
                    f"cannot be started from {status}."
                ),
            )

        self.stop_requested = False
        self.paused = False

        self.task = asyncio.create_task(
            self._run(campaign["id"])
        )

        return True, "Campaign started."

    async def stop(self):

        if not self.running:
            return "Campaign is not running."

        self.stop_requested = True
        self.paused = False

        return "Stop requested."

    def pause(self):

        if not self.running:
            return "Campaign is not running."

        self.paused = True

        return "Campaign paused."

    def resume(self):

        if not self.running:
            return "Campaign is not running."

        self.paused = False

        return "Campaign resumed."

    async def _wait_if_paused(self):

        while self.paused and not self.stop_requested:
            await asyncio.sleep(1)

    async def _cooldown(
        self,
        seconds: int,
    ) -> bool:

        seconds = max(0, seconds)

        remaining = seconds

        while remaining > 0:

            if self.stop_requested:
                return False

            await self._wait_if_paused()

            if self.stop_requested:
                return False

            await asyncio.sleep(1)

            remaining -= 1

        return True

    def _read_setting(
        self,
        key: str,
        default: int,
        minimum: int,
    ) -> int:

        raw_value = self.db.get_setting(
            key,
            str(default),
        )

        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            value = default

        return max(minimum, value)

    async def _run(
        self,
        campaign_id: int,
    ):

        campaign = self.db.get_campaign(
            campaign_id
        )

        if campaign is None:
            self.task = None
            return

        repeat_count = max(
            1,
            int(campaign["repeat_count"]),
        )

        target_cooldown = self._read_setting(
            key="target_cooldown",
            default=60,
            minimum=10,
        )

        round_cooldown = self._read_setting(
            key="round_cooldown",
            default=3600,
            minimum=60,
        )

        current_round = int(
            campaign["current_round"] or 0
        )

        start_round = (
            current_round
            if current_round >= 1
            else 1
        )

        self.db.mark_campaign_started(
            campaign_id
        )

        try:

            for round_number in range(
                start_round,
                repeat_count + 1,
            ):

                if self.stop_requested:
                    break

                self.db.set_campaign_round(
                    campaign_id,
                    round_number,
                )

                self.db.prepare_campaign_targets(
                    campaign_id,
                    round_number,
                )

                pending = (
                    self.db.get_pending_targets(
                        campaign_id,
                        round_number,
                    )
                )

                for target in pending:

                    if self.stop_requested:
                        break

                    await self._wait_if_paused()

                    if self.stop_requested:
                        break

                    try:

                        await self.app.send_message(
                            target["chat_id"],
                            campaign["message"],
                        )

                        self.db.mark_campaign_target_sent(
                            target["id"]
                        )

                        self.db.mark_sent(
                            target["chat_id"]
                        )

                        self.db.log_event(
                            "SEND",
                            (
                                f"Campaign {campaign_id}: "
                                f"sent to {target['title']}"
                            ),
                        )

                    except FloodWait as error:

                        self.db.mark_campaign_target_failed(
                            target["id"],
                            f"FloodWait: {error.value}s",
                        )

                        self.db.log_event(
                            "FLOOD_WAIT",
                            (
                                "Telegram requested "
                                f"{error.value}s wait."
                            ),
                        )

                        if not await self._cooldown(
                            error.value
                        ):
                            break

                    except Exception as error:

                        self.db.mark_campaign_target_failed(
                            target["id"],
                            str(error),
                        )

                        self.db.log_event(
                            "SEND_ERROR",
                            (
                                f"{target['title']}: "
                                f"{error}"
                            ),
                        )

                    if not await self._cooldown(
                        target_cooldown
                    ):
                        break

                if self.stop_requested:
                    break

                if round_number < repeat_count:

                    self.db.update_campaign_status(
                        campaign_id,
                        "ROUND_WAIT",
                    )

                    if not await self._cooldown(
                        round_cooldown
                    ):
                        break

            if self.stop_requested:

                self.db.mark_campaign_completed(
                    campaign_id,
                    status="STOPPED",
                )

            else:

                self.db.mark_campaign_completed(
                    campaign_id,
                    status="COMPLETED",
                )

        except Exception as error:

            self.db.mark_campaign_completed(
                campaign_id,
                status="FAILED",
            )

            self.db.log_event(
                "CAMPAIGN_ERROR",
                str(error),
            )

        finally:

            self.task = None
            self.stop_requested = False
            self.paused = False