from .campaign.manager import CampaignManager
from .config import DATA_DIR, validate_config
from .database.db import Database
from .telegram.client import app
from .telegram.handlers import register_handlers


def main() -> None:
    validate_config()

    db_path = DATA_DIR / "bot.db"

    db = Database(db_path)

    campaign_manager = CampaignManager(
        app=app,
        db=db,
    )

    register_handlers(
        app=app,
        db=db,
        campaign_manager=campaign_manager,
    )

    print("=" * 50)
    print("Telegram Ad Userbot")
    print("=" * 50)
    print(f"Database: {db_path}")
    print("Library: Hydrogram")
    print("Control panel: Saved Messages")
    print("=" * 50)

    app.run()


if __name__ == "__main__":
    main()