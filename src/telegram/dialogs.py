from hydrogram import raw


def _to_marked_channel_id(
    raw_channel_id: int,
) -> int:
    """
    Convert a raw Telegram channel/supergroup ID (positive)
    to the marked peer ID used by Hydrogram (-100xxxxxxxxxx).
    """
    return int(f"-100{raw_channel_id}")


def _build_channel_map(chats):
    return {
        chat.id: chat
        for chat in chats
        if isinstance(
            chat,
            raw.types.Channel,
        )
    }


def _build_offset_peer(
    last_dialog,
    channel_map,
):
    """
    Build the InputPeer needed to continue GetDialogs
    pagination from the last dialog we received.
    """

    peer = last_dialog.peer

    if isinstance(
        peer,
        raw.types.PeerChannel,
    ):
        chat = channel_map.get(
            peer.channel_id
        )

        access_hash = (
            chat.access_hash
            if chat
            else 0
        )

        return raw.types.InputPeerChannel(
            channel_id=peer.channel_id,
            access_hash=access_hash,
        )

    if isinstance(
        peer,
        raw.types.PeerUser,
    ):
        return raw.types.InputPeerUser(
            user_id=peer.user_id,
            access_hash=0,
        )

    if isinstance(
        peer,
        raw.types.PeerChat,
    ):
        return raw.types.InputPeerChat(
            chat_id=peer.chat_id,
        )

    return raw.types.InputPeerEmpty()


async def _iter_archived_dialogs(app):
    """
    Async generator yielding every GetDialogs response
    for the Archive folder, handling pagination.

    Each dialog returned here is guaranteed by Telegram
    to belong to folder 1 (Archive).
    """

    offset_id = 0
    offset_date = 0
    offset_peer = raw.types.InputPeerEmpty()

    while True:

        result = await app.invoke(
            raw.functions.messages.GetDialogs(
                offset_date=offset_date,
                offset_id=offset_id,
                offset_peer=offset_peer,
                limit=100,
                hash=0,
                folder_id=1,
            )
        )

        if not result.dialogs:
            return

        yield result

        if len(result.dialogs) < 100:
            return

        last_dialog = result.dialogs[-1]

        channel_map = _build_channel_map(
            result.chats
        )

        offset_peer = _build_offset_peer(
            last_dialog,
            channel_map,
        )

        offset_id = (
            last_dialog.top_message or 0
        )

        offset_date = 0


async def sync_archived_groups(app, db) -> int:
    """
    Sync only supergroups that Telegram reports inside Archive.

    Broadcast channels, private users and bots are ignored.

    A dialog is considered archived ONLY if its raw
    `folder_id` field equals 1 (Telegram's Archive folder).
    """

    found = {}

    async for result in _iter_archived_dialogs(app):

        channel_map = _build_channel_map(
            result.chats
        )

        for dialog in result.dialogs:

            # 🔴 KEY FIX: only accept dialogs that are
            # actually inside folder 1 (Archive).
            if dialog.folder_id != 1:
                continue

            peer = dialog.peer

            if not isinstance(
                peer,
                raw.types.PeerChannel,
            ):
                continue

            chat = channel_map.get(
                peer.channel_id
            )

            if chat is None:
                continue

            # Broadcast channels are excluded.
            if not chat.megagroup:
                continue

            found[chat.id] = {
                "chat_id": _to_marked_channel_id(
                    chat.id
                ),
                "title": (
                    chat.title or "Unknown"
                ),
                "username": chat.username,
            }

    targets = list(found.values())

    db.sync_targets(targets)

    return len(targets)