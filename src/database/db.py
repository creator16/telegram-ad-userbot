import sqlite3
from pathlib import Path
from typing import Optional


class Database:
    def __init__(self, path: Path):
        self.path = path

        self.conn = sqlite3.connect(
            self.path,
            check_same_thread=False,
        )

        self.conn.row_factory = sqlite3.Row

        self._create_tables()

    def _create_tables(self) -> None:
        cursor = self.conn.cursor()

        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS targets (
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                username TEXT,
                is_group INTEGER DEFAULT 1,
                archived INTEGER DEFAULT 0,
                enabled INTEGER DEFAULT 1,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_sent_at TEXT,
                send_count INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                repeat_count INTEGER DEFAULT 1,
                current_round INTEGER DEFAULT 0,
                status TEXT DEFAULT 'READY',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                started_at TEXT,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS campaign_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                status TEXT DEFAULT 'PENDING',
                sent_at TEXT,
                error TEXT,
                retry_count INTEGER DEFAULT 0,
                UNIQUE(
                    campaign_id,
                    chat_id,
                    round_number
                )
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        self.conn.commit()

    # -------------------------
    # Settings
    # -------------------------

    def set_setting(self, key: str, value: str) -> None:
        self.conn.execute(
            """
            INSERT INTO settings(key, value)
            VALUES (?, ?)
            ON CONFLICT(key)
            DO UPDATE SET value=excluded.value
            """,
            (key, value),
        )

        self.conn.commit()

    def get_setting(
        self,
        key: str,
        default: Optional[str] = None,
    ) -> Optional[str]:
        row = self.conn.execute(
            """
            SELECT value
            FROM settings
            WHERE key = ?
            """,
            (key,),
        ).fetchone()

        if row is None:
            return default

        return row["value"]

    # -------------------------
    # Targets
    # -------------------------

    def upsert_target(
        self,
        chat_id: int,
        title: str,
        username: Optional[str],
        archived: bool,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO targets(
                chat_id,
                title,
                username,
                archived
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(chat_id)
            DO UPDATE SET
                title=excluded.title,
                username=excluded.username,
                archived=excluded.archived
            """,
            (
                chat_id,
                title,
                username,
                int(archived),
            ),
        )

        self.conn.commit()

    def mark_all_targets_unarchived(self) -> None:
        self.conn.execute(
            """
            UPDATE targets
            SET archived = 0
            """
        )

        self.conn.commit()

    def get_targets(self):
        return self.conn.execute(
            """
            SELECT *
            FROM targets
            WHERE enabled = 1
              AND archived = 1
            ORDER BY title COLLATE NOCASE
            """
        ).fetchall()

    def get_target(self, chat_id: int):
        return self.conn.execute(
            """
            SELECT *
            FROM targets
            WHERE chat_id = ?
            """,
            (chat_id,),
        ).fetchone()

    def mark_sent(self, chat_id: int) -> None:
        self.conn.execute(
            """
            UPDATE targets
            SET
                last_sent_at = CURRENT_TIMESTAMP,
                send_count = send_count + 1
            WHERE chat_id = ?
            """,
            (chat_id,),
        )

        self.conn.commit()

    # -------------------------
    # Campaigns
    # -------------------------

    def create_campaign(
        self,
        message: str,
        repeat_count: int,
    ) -> int:
        cursor = self.conn.execute(
            """
            INSERT INTO campaigns(
                message,
                repeat_count
            )
            VALUES (?, ?)
            """,
            (
                message,
                repeat_count,
            ),
        )

        self.conn.commit()

        return cursor.lastrowid

    def get_campaign(self, campaign_id: int):
        return self.conn.execute(
            """
            SELECT *
            FROM campaigns
            WHERE id = ?
            """,
            (campaign_id,),
        ).fetchone()

    def get_latest_campaign(self):
        return self.conn.execute(
            """
            SELECT *
            FROM campaigns
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    def update_campaign_status(
        self,
        campaign_id: int,
        status: str,
    ) -> None:
        self.conn.execute(
            """
            UPDATE campaigns
            SET status = ?
            WHERE id = ?
            """,
            (
                status,
                campaign_id,
            ),
        )

        self.conn.commit()

    def mark_campaign_started(
        self,
        campaign_id: int,
    ) -> None:
        self.conn.execute(
            """
            UPDATE campaigns
            SET
                status = 'RUNNING',
                started_at = COALESCE(
                    started_at,
                    CURRENT_TIMESTAMP
                ),
                completed_at = NULL
            WHERE id = ?
            """,
            (campaign_id,),
        )

        self.conn.commit()

    def mark_campaign_completed(
        self,
        campaign_id: int,
        status: str = "COMPLETED",
    ) -> None:
        self.conn.execute(
            """
            UPDATE campaigns
            SET
                status = ?,
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                status,
                campaign_id,
            ),
        )

        self.conn.commit()

    def set_campaign_round(
        self,
        campaign_id: int,
        round_number: int,
    ) -> None:
        self.conn.execute(
            """
            UPDATE campaigns
            SET current_round = ?
            WHERE id = ?
            """,
            (
                round_number,
                campaign_id,
            ),
        )

        self.conn.commit()

    # -------------------------
    # Campaign targets
    # -------------------------

    def prepare_campaign_targets(
        self,
        campaign_id: int,
        round_number: int,
    ) -> None:
        targets = self.get_targets()

        for target in targets:
            self.conn.execute(
                """
                INSERT OR IGNORE INTO campaign_targets(
                    campaign_id,
                    chat_id,
                    round_number
                )
                VALUES (?, ?, ?)
                """,
                (
                    campaign_id,
                    target["chat_id"],
                    round_number,
                ),
            )

        self.conn.commit()

    def get_pending_targets(
        self,
        campaign_id: int,
        round_number: int,
    ):
        return self.conn.execute(
            """
            SELECT
                ct.*,
                t.title,
                t.username
            FROM campaign_targets ct
            JOIN targets t
                ON t.chat_id = ct.chat_id
            WHERE ct.campaign_id = ?
              AND ct.round_number = ?
              AND ct.status = 'PENDING'
              AND t.enabled = 1
              AND t.archived = 1
            ORDER BY t.title COLLATE NOCASE
            """,
            (
                campaign_id,
                round_number,
            ),
        ).fetchall()

    def mark_campaign_target_sent(
        self,
        campaign_target_id: int,
    ) -> None:
        self.conn.execute(
            """
            UPDATE campaign_targets
            SET
                status = 'SENT',
                sent_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (campaign_target_id,),
        )

        self.conn.commit()

    def mark_campaign_target_failed(
        self,
        campaign_target_id: int,
        error: str,
    ) -> None:
        self.conn.execute(
            """
            UPDATE campaign_targets
            SET
                status = 'FAILED',
                error = ?,
                retry_count = retry_count + 1
            WHERE id = ?
            """,
            (
                error,
                campaign_target_id,
            ),
        )

        self.conn.commit()

    # -------------------------
    # Events
    # -------------------------

    def log_event(
        self,
        event_type: str,
        message: str,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO events(
                event_type,
                message
            )
            VALUES (?, ?)
            """,
            (
                event_type,
                message,
            ),
        )

        self.conn.commit()

    def history(self, limit: int = 20):
        return self.conn.execute(
            """
            SELECT *
            FROM events
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()