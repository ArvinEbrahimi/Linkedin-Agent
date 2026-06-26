"""LinkedIn OAuth 2.0 / OpenID Connect (Sign In with LinkedIn)."""

from __future__ import annotations

import json
import logging
import secrets
import sqlite3
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx

from app.config import Settings
from app.core.exceptions import ConfigurationError, LinkAidError
from app.models.linkedin import LinkedInUserInfo
from app.models.user import UserProfile
from app.services.memory_store import MemoryService, _sqlite_path_from_url

logger = logging.getLogger(__name__)

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
SCOPES = "openid profile email"


class LinkedInOAuthError(LinkAidError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="linkedin_oauth_error")


class LinkedInOAuthService:
    def __init__(self, settings: Settings, memory_service: MemoryService) -> None:
        self.settings = settings
        self.memory = memory_service
        self.db_path = _sqlite_path_from_url(settings.database_url)
        self._init_tables()

    def _init_tables(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS oauth_states (
                    state TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS linkedin_accounts (
                    user_id TEXT PRIMARY KEY,
                    linkedin_sub TEXT UNIQUE NOT NULL,
                    access_token TEXT NOT NULL,
                    token_expires_at TEXT,
                    profile_json TEXT NOT NULL,
                    connected_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _ensure_configured(self) -> None:
        if not self.settings.linkedin_oauth_configured:
            raise ConfigurationError(
                "LinkedIn OAuth is not configured. Set LINKEDIN_CLIENT_ID and "
                "LINKEDIN_CLIENT_SECRET in .env - see docs/LINKEDIN_SETUP.md"
            )

    def create_auth_url(self, user_id: str) -> tuple[str, str]:
        self._ensure_configured()
        state = secrets.token_urlsafe(32)
        expires = (datetime.now(UTC) + timedelta(minutes=10)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO oauth_states (state, user_id, expires_at) VALUES (?, ?, ?)",
                (state, user_id, expires),
            )
            conn.commit()

        params = {
            "response_type": "code",
            "client_id": self.settings.linkedin_client_id,
            "redirect_uri": self.settings.linkedin_redirect_uri,
            "scope": SCOPES,
            "state": state,
        }
        return f"{LINKEDIN_AUTH_URL}?{urlencode(params)}", state

    def _pop_user_id_for_state(self, state: str) -> str:
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT user_id, expires_at FROM oauth_states WHERE state = ?", (state,)
            ).fetchone()
            if not row:
                raise LinkedInOAuthError("Invalid or expired OAuth state")
            user_id, expires_at = row
            if expires_at < now:
                conn.execute("DELETE FROM oauth_states WHERE state = ?", (state,))
                conn.commit()
                raise LinkedInOAuthError("OAuth state expired — try connecting again")
            conn.execute("DELETE FROM oauth_states WHERE state = ?", (state,))
            conn.commit()
        return user_id

    async def handle_callback(self, code: str, state: str) -> tuple[str, LinkedInUserInfo]:
        self._ensure_configured()
        user_id = self._pop_user_id_for_state(state)
        token_data = await self._exchange_code(code)
        userinfo = await self._fetch_userinfo(token_data["access_token"])
        self._save_account(user_id, token_data, userinfo)
        self._merge_profile(user_id, userinfo)
        logger.info("LinkedIn connected user=%s sub=%s", user_id, userinfo.sub)
        return user_id, userinfo

    async def _exchange_code(self, code: str) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                LINKEDIN_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": self.settings.linkedin_client_id,
                    "client_secret": self.settings.linkedin_client_secret,
                    "redirect_uri": self.settings.linkedin_redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if response.status_code >= 400:
            raise LinkedInOAuthError(f"Token exchange failed: {response.text}")
        return response.json()

    async def _fetch_userinfo(self, access_token: str) -> LinkedInUserInfo:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                LINKEDIN_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if response.status_code >= 400:
            raise LinkedInOAuthError(f"Userinfo fetch failed: {response.text}")
        return LinkedInUserInfo.model_validate(response.json())

    def _save_account(
        self, user_id: str, token_data: dict, userinfo: LinkedInUserInfo
    ) -> None:
        now = datetime.now(UTC).isoformat()
        expires_in = token_data.get("expires_in")
        token_expires = None
        if expires_in:
            token_expires = (datetime.now(UTC) + timedelta(seconds=int(expires_in))).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO linkedin_accounts
                    (user_id, linkedin_sub, access_token, token_expires_at,
                     profile_json, connected_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    linkedin_sub = excluded.linkedin_sub,
                    access_token = excluded.access_token,
                    token_expires_at = excluded.token_expires_at,
                    profile_json = excluded.profile_json,
                    updated_at = excluded.updated_at
                """,
                (
                    user_id,
                    userinfo.sub,
                    token_data["access_token"],
                    token_expires,
                    userinfo.model_dump_json(),
                    now,
                    now,
                ),
            )
            conn.commit()

    def _merge_profile(self, user_id: str, userinfo: LinkedInUserInfo) -> None:
        existing = self.memory.get_profile(user_id)
        profile = existing or UserProfile(user_id=user_id)
        profile.linkedin_sub = userinfo.sub
        profile.email = userinfo.email or profile.email
        if userinfo.name:
            profile.name = userinfo.name
        elif userinfo.given_name:
            profile.name = userinfo.given_name
        self.memory.save_profile(user_id, profile)

    def get_status(self, user_id: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT linkedin_sub, profile_json, connected_at
                FROM linkedin_accounts WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
        if not row:
            return {"user_id": user_id, "connected": False}

        sub, profile_json, connected_at = row
        info = LinkedInUserInfo.model_validate(json.loads(profile_json))
        return {
            "user_id": user_id,
            "connected": True,
            "linkedin_sub": sub,
            "name": info.name,
            "email": info.email,
            "picture": info.picture,
            "connected_at": connected_at,
            "import_available": True,
        }

    def disconnect(self, user_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM linkedin_accounts WHERE user_id = ?", (user_id,))
            conn.commit()
        profile = self.memory.get_profile(user_id)
        if profile:
            profile.linkedin_sub = None
            self.memory.save_profile(user_id, profile)
