from pyrogram.enums import ChatType


GROUP_TYPES = {
    ChatType.GROUP,
    ChatType.SUPERGROUP,
}


async def sync_archived_groups(app, db) -> int:
    """
    Synchronize the user's currently archived groups.

    This function does not join, leave, archive, or unarchive anything.
    It only reads the current Telegram dialog state.
    """

    db.mark_all_targets_unarchived()

    count = 0

    async for dialog in app.get_dialogs():
        chat = dialog.chat

        if chat.type not in GROUP_TYPES:
            continue

        archived = getattr(
            dialog,
            "folder_id",
            None,
        ) == 1

        if not archived:
            continue

        db.upsert_target(
            chat_id=chat.id,
            title=chat.title or "Unknown",
            username=chat.username,
            archived=True,
        )

        count += 1

    return count


async def list_archived_groups(app):
    """Return currently archived groups."""

    results = []

    async for dialog in app.get_dialogs():
        chat = dialog.chat

        if chat.type not in GROUP_TYPES:
            continue

        archived = getattr(
            dialog,
            "folder_id",
            None,
        ) == 1

        if archived:
            results.append(chat)

    return results