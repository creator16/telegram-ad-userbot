import asyncio
from datetime import datetime

from pyrogram.errors import FloodWait


class CampaignManager:

    def __init__(self, app, db):
        self.app = app
        self.db = db

        self.task = None

        self.paused = False
        self.stop_requested = False

    @property
    def running(self):
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

        if campaign["status"] == "COMPLETED":
            return False, "Latest campaign is already completed."

        self.stop_requested = False
        self.paused = False

        self.task = asyncio.create_task(
            self._run(campaign["id"])
        )

        return True, "Campaign started."

    async def stop(self):
        self.stop_requested = True
        self.paused = False

        if self.task:
            await asyncio.sleep(0)

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

    async def _cooldown(self, seconds: int):

        remaining = seconds

        while remaining > 0:

            if self.stop_requested:
                return False

            await self._wait_if_paused()

            await asyncio.sleep(1)

            remaining -= 1

        return True

    async def _run(self, campaign_id: int):

        campaign = self.db.get_campaign(campaign_id)

        if campaign is None:
            return

        repeat_count = max(
            1,
            int(campaign["repeat_count"]),
        )

        target_cooldown = int(
            self.db.get_setting(
                "target_cooldown",
                "60",
            )
        )

        round_cooldown = int(
            self.db.get_setting(
                "round_cooldown",
                "3600",
            )
        )

        self.db.update_campaign_status(
            campaign_id,
            "RUNNING",
        )

        try:

            for round_number in range(
                1,
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

                pending = self.db.get_pending_targets(
                    campaign_id,
                    round_number,
                )

                for target in pending:

                    if self.stop_requested:
                        break

                    await self._wait_if_paused()

                    chat_id = target["chat_id"]

                    try:

                        await self.app.send_message(
                            chat_id,
                            campaign["message"],
                        )

                        self.db.mark_campaign_target_sent(
                            target["id"]
                        )

                        self.db.mark_sent(chat_id)

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
                                f"Telegram requested "
                                f"{error.value}s wait."
                            ),
                        )

                        await asyncio.sleep(
                            error.value
                        )

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

                    await self._cooldown(
                        round_cooldown
                    )

                    self.db.update_campaign_status(
                        campaign_id,
                        "RUNNING",
                    )

            if self.stop_requested:

                self.db.update_campaign_status(
                    campaign_id,
                    "STOPPED",
                )

            else:

                self.db.update_campaign_status(
                    campaign_id,
                    "COMPLETED",
                )

        except Exception as error:

            self.db.update_campaign_status(
                campaign_id,
                "FAILED",
            )

            self.db.log_event(
                "CAMPAIGN_ERROR",
                str(error),
            )

        finally:

            self.task = None
            self.stop_requested = False
            self.paused = False