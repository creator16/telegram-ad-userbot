import re

from pyrogram import filters

from .dialogs import sync_archived_groups


HELP_TEXT = """
📢 Telegram Ad Userbot

Commands:

$HELP
$STATUS
$SYNC
$QUEUE
$START
$STOP
$PAUSE
$RESUME
$CANCEL
$HISTORY

Settings:

$TARGET_COOLDOWN 60
$ROUND_COOLDOWN 3600
$REPEAT 1

Create campaign:

$MESSAGE
Your advertising message here
$$

Then:

$START

Only archived groups are used as targets.
"""


def register_handlers(app, db, campaign_manager):

    @app.on_message(
        filters.me
        & filters.private
        & filters.chat("me")
    )
    async def command_handler(client, message):

        text = message.text or ""

        command = text.strip()

        # -------------------------
        # HELP
        # -------------------------

        if command.upper() == "$HELP":

            await message.reply_text(
                HELP_TEXT
            )

            return

        # -------------------------
        # STATUS
        # -------------------------

        if command.upper() == "$STATUS":

            campaign = db.get_latest_campaign()

            targets = db.get_targets()

            if campaign:

                status = campaign["status"]
                round_number = campaign["current_round"]
                repeat = campaign["repeat_count"]

                campaign_info = (
                    f"Campaign: #{campaign['id']}\n"
                    f"Status: {status}\n"
                    f"Round: {round_number}/{repeat}"
                )

            else:

                campaign_info = (
                    "Campaign: none"
                )

            await message.reply_text(
                "📊 STATUS\n\n"
                f"{campaign_info}\n\n"
                f"Archived targets: {len(targets)}\n"
                f"Running: {campaign_manager.running}\n"
                f"Paused: {campaign_manager.paused}"
            )

            return

        # -------------------------
        # SYNC
        # -------------------------

        if command.upper() == "$SYNC":

            count = await sync_archived_groups(
                client,
                db,
            )

            await message.reply_text(
                f"✅ Synced {count} archived groups."
            )

            return

        # -------------------------
        # QUEUE
        # -------------------------

        if command.upper() == "$QUEUE":

            targets = db.get_targets()

            if not targets:

                await message.reply_text(
                    "Queue is empty."
                )

                return

            lines = ["📋 TARGET QUEUE\n"]

            for index, target in enumerate(
                targets,
                start=1,
            ):

                username = (
                    f"@{target['username']}"
                    if target["username"]
                    else "-"
                )

                lines.append(
                    f"{index}. "
                    f"{target['title']} "
                    f"{username}"
                )

            await message.reply_text(
                "\n".join(lines)
            )

            return

        # -------------------------
        # TARGET COOLDOWN
        # -------------------------

        match = re.fullmatch(
            r"\$TARGET_COOLDOWN\s+(\d+)",
            command,
            flags=re.IGNORECASE,
        )

        if match:

            seconds = int(match.group(1))

            if seconds < 10:
                await message.reply_text(
                    "Minimum cooldown is 10 seconds."
                )
                return

            db.set_setting(
                "target_cooldown",
                str(seconds),
            )

            await message.reply_text(
                f"✅ Target cooldown: {seconds}s"
            )

            return

        # -------------------------
        # ROUND COOLDOWN
        # -------------------------

        match = re.fullmatch(
            r"\$ROUND_COOLDOWN\s+(\d+)",
            command,
            flags=re.IGNORECASE,
        )

        if match:

            seconds = int(match.group(1))

            if seconds < 60:
                await message.reply_text(
                    "Minimum round cooldown is 60 seconds."
                )
                return

            db.set_setting(
                "round_cooldown",
                str(seconds),
            )

            await message.reply_text(
                f"✅ Round cooldown: {seconds}s"
            )

            return

        # -------------------------
        # REPEAT
        # -------------------------

        match = re.fullmatch(
            r"\$REPEAT\s+(\d+)",
            command,
            flags=re.IGNORECASE,
        )

        if match:

            repeat = int(match.group(1))

            if repeat < 1 or repeat > 50:

                await message.reply_text(
                    "Repeat must be between 1 and 50."
                )

                return

            db.set_setting(
                "repeat",
                str(repeat),
            )

            await message.reply_text(
                f"✅ Repeat count: {repeat}"
            )

            return

        # -------------------------
        # MESSAGE
        # -------------------------

        if command.upper().startswith("$MESSAGE"):

            body = command[len("$MESSAGE"):].strip()

            if body.startswith("\n"):
                body = body.strip()

            if body.endswith("$$"):
                body = body[:-2].strip()

            if not body:

                await message.reply_text(
                    "Message is empty."
                )

                return

            repeat = int(
                db.get_setting(
                    "repeat",
                    "1",
                )
            )

            campaign_id = db.create_campaign(
                message=body,
                repeat_count=repeat,
            )

            await message.reply_text(
                "✅ Campaign created.\n\n"
                f"Campaign ID: {campaign_id}\n"
                f"Repeat: {repeat}\n\n"
                "Use $START when ready."
            )

            return

        # -------------------------
        # START
        # -------------------------

        if command.upper() == "$START":

            success, result = (
                await campaign_manager.start()
            )

            await message.reply_text(
                (
                    "▶️ " if success else "⚠️ "
                ) + result
            )

            return

        # -------------------------
        # STOP
        # -------------------------

        if command.upper() == "$STOP":

            result = await campaign_manager.stop()

            await message.reply_text(
                f"⏹ {result}"
            )

            return

        # -------------------------
        # PAUSE
        # -------------------------

        if command.upper() == "$PAUSE":

            result = campaign_manager.pause()

            await message.reply_text(
                f"⏸ {result}"
            )

            return

        # -------------------------
        # RESUME
        # -------------------------

        if command.upper() == "$RESUME":

            result = campaign_manager.resume()

            await message.reply_text(
                f"▶️ {result}"
            )

            return

        # -------------------------
        # CANCEL
        # -------------------------

        if command.upper() == "$CANCEL":

            if campaign_manager.running:

                await message.reply_text(
                    "⚠️ Stop the running campaign first."
                )

                return

            campaign = db.get_latest_campaign()

            if campaign is None:

                await message.reply_text(
                    "No campaign."
                )

                return

            db.update_campaign_status(
                campaign["id"],
                "CANCELLED",
            )

            await message.reply_text(
                f"❌ Campaign #{campaign['id']} cancelled."
            )

            return

        # -------------------------
        # HISTORY
        # -------------------------

        if command.upper() == "$HISTORY":

            events = db.history(20)

            if not events:

                await message.reply_text(
                    "History is empty."
                )

                return

            lines = ["📜 HISTORY\n"]

            for event in events:

                lines.append(
                    f"[{event['created_at']}] "
                    f"{event['event_type']}\n"
                    f"{event['message']}"
                )

            await message.reply_text(
                "\n\n".join(lines)
            )

            return