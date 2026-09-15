from hydrogram import raw


def _get_channel_map(chats):
    return {
        chat.id: chat
        for chat in chats
        if isinstance(
            chat,
            raw.types.Channel,
        )
    }


async def sync_archived_groups(app, db) -> int:
    """
    Sync only groups that Telegram reports inside Archive.

    Channels, private users and bots are ignored.
    """

    db.mark_all_targets_unarchived()

    result = await app.invoke(
        raw.functions.messages.GetDialogs(
            offset_date=0,
            offset_id=0,
            offset_peer=raw.types.InputPeerEmpty(),
            limit=100,
            hash=0,
            folder_id=1,
        )
    )

    channel_map = _get_channel_map(
        result.chats
    )

    count = 0

    for dialog in result.dialogs:

        peer = dialog.peer

        if not isinstance(
            peer,
            raw.types.PeerChannel,
        ):
            continue

        channel_id = peer.channel_id

        chat = channel_map.get(
            channel_id
        )

        if chat is None:
            continue

        # Broadcast channels are excluded.
        if not chat.megagroup:
            continue

        db.upsert_target(
            chat_id=chat.id,
            title=chat.title or "Unknown",
            username=chat.username,
            archived=True,
        )

        count += 1

    return count