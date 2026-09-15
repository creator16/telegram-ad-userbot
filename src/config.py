import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


def _get_api_id() -> int:
    raw_value = os.getenv(
        "TELEGRAM_API_ID",
        "",
    ).strip()

    if not raw_value:
        return 0

    try:
        return int(raw_value)
    except ValueError:
        return 0


API_ID = _get_api_id()

API_HASH = os.getenv(
    "TELEGRAM_API_HASH",
    "",
).strip()

SESSION_NAME = os.getenv(
    "TELEGRAM_SESSION_NAME",
    "telegram_ad_userbot",
).strip()

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def validate_config() -> None:
    """Validate required Telegram configuration."""

    if API_ID <= 0:
        raise ValueError(
            "TELEGRAM_API_ID is missing or invalid in .env"
        )

    if not API_HASH:
        raise ValueError(
            "TELEGRAM_API_HASH is missing in .env"
        )

    if not SESSION_NAME:
        raise ValueError(
            "TELEGRAM_SESSION_NAME cannot be empty"
        )