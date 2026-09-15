import pyrogram.utils


# Pyrogram 2.0.106 uses outdated Telegram peer ID boundaries.
# These values come from the compatibility update proposed
# in the official Pyrogram repository.
MIN_CHANNEL_ID = -1007852516352
MIN_CHAT_ID = -999999999999


def apply_pyrogram_compatibility_patch() -> None:
    """
    Update outdated peer ID boundaries used by Pyrogram 2.0.106.
    """

    pyrogram.utils.MIN_CHANNEL_ID = MIN_CHANNEL_ID
    pyrogram.utils.MIN_CHAT_ID = MIN_CHAT_ID