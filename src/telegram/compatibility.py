import hydrogram.utils


# Pyrogram 2.0.106 / Hydrogram use outdated Telegram
# peer ID boundaries. These values come from the
# compatibility update proposed in the official
# Pyrogram repository.
MIN_CHANNEL_ID = -1007852516352
MIN_CHAT_ID = -999999999999


def apply_compatibility_patch() -> None:
    """
    Update outdated peer ID boundaries used by Hydrogram.
    """

    hydrogram.utils.MIN_CHANNEL_ID = MIN_CHANNEL_ID
    hydrogram.utils.MIN_CHAT_ID = MIN_CHAT_ID