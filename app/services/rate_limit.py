import logging
import sqlite3
from datetime import date
from pathlib import Path

from app.core.exceptions import RateLimitError

logger = logging.getLogger(__name__)

DEFAULT_DAILY_LIMIT = 20


class OutreachRateLimiter:
    """SQLite-backed daily outreach counter per user."""

    def __init__(self, db_path: str, daily_limit: int = DEFAULT_DAILY_LIMIT) -> None:
        self.db_path = db_path
        self.daily_limit = daily_limit
        self._init_db()

    def _init_db(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS outreach_daily (
                    user_id TEXT NOT NULL,
                    day TEXT NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (user_id, day)
                )
                """
            )
            conn.commit()

    def get_count(self, user_id: str, day: date | None = None) -> int:
        day_str = (day or date.today()).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT count FROM outreach_daily WHERE user_id = ? AND day = ?",
                (user_id, day_str),
            ).fetchone()
        return row[0] if row else 0

    def remaining(self, user_id: str) -> int:
        return max(0, self.daily_limit - self.get_count(user_id))

    def check_and_increment(self, user_id: str) -> int:
        """Increment counter if under limit. Returns remaining after increment."""
        day_str = date.today().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT count FROM outreach_daily WHERE user_id = ? AND day = ?",
                (user_id, day_str),
            ).fetchone()
            current = row[0] if row else 0

            if current >= self.daily_limit:
                raise RateLimitError(
                    f"Daily outreach limit reached ({self.daily_limit}/day). "
                    "Try again tomorrow."
                )

            new_count = current + 1
            conn.execute(
                """
                INSERT INTO outreach_daily (user_id, day, count) VALUES (?, ?, ?)
                ON CONFLICT(user_id, day) DO UPDATE SET count = excluded.count
                """,
                (user_id, day_str, new_count),
            )
            conn.commit()

        remaining = self.daily_limit - new_count
        logger.info("Outreach count user=%s count=%d remaining=%d", user_id, new_count, remaining)
        return remaining

    def reset_user(self, user_id: str, day: date | None = None) -> None:
        """Reset counter — for testing only."""
        day_str = (day or date.today()).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM outreach_daily WHERE user_id = ? AND day = ?",
                (user_id, day_str),
            )
            conn.commit()
