"""User account storage in the primary application database."""

from __future__ import annotations

import logging
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.config import Settings
from app.services.memory_store import _sqlite_path_from_url

logger = logging.getLogger(__name__)


@dataclass
class Account:
    id: str
    email: str
    display_name: str
    created_at: str


class AuthStore:
    def __init__(self, settings: Settings) -> None:
        self.db_path = _sqlite_path_from_url(settings.database_url)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def create_account(self, email: str, password_hash: str, display_name: str) -> Account:
        account_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        normalized_email = email.strip().lower()
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO accounts (id, email, password_hash, display_name, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (account_id, normalized_email, password_hash, display_name.strip(), now),
                )
                conn.commit()
            except sqlite3.IntegrityError as exc:
                raise ValueError("email_already_registered") from exc
        return Account(
            id=account_id,
            email=normalized_email,
            display_name=display_name.strip(),
            created_at=now,
        )

    def get_by_email(self, email: str) -> tuple[Account, str] | None:
        normalized_email = email.strip().lower()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT id, email, password_hash, display_name, created_at
                FROM accounts WHERE email = ?
                """,
                (normalized_email,),
            ).fetchone()
        if not row:
            return None
        account = Account(
            id=row[0],
            email=row[1],
            display_name=row[3],
            created_at=row[4],
        )
        return account, row[2]

    def get_by_id(self, account_id: str) -> Account | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT id, email, display_name, created_at
                FROM accounts WHERE id = ?
                """,
                (account_id,),
            ).fetchone()
        if not row:
            return None
        return Account(id=row[0], email=row[1], display_name=row[2], created_at=row[3])

    def account_count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()
        return int(row[0]) if row else 0

    def export_public(self, account: Account) -> dict:
        return {
            "user_id": account.id,
            "email": account.email,
            "display_name": account.display_name,
            "created_at": account.created_at,
        }
