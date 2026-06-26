"""JWT authentication and password hashing."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.config import Settings
from app.core.exceptions import LinkAidError
from app.services.auth_store import Account, AuthStore


class AuthError(LinkAidError):
    def __init__(self, message: str, code: str = "auth_error") -> None:
        super().__init__(message, code=code)


class AuthService:
    def __init__(self, settings: Settings, store: AuthStore | None = None) -> None:
        self.settings = settings
        self.store = store or AuthStore(settings)

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

    def create_access_token(self, user_id: str) -> str:
        expire = datetime.now(UTC) + timedelta(days=self.settings.jwt_expire_days)
        payload = {"sub": user_id, "exp": expire}
        return jwt.encode(payload, self.settings.app_secret_key, algorithm="HS256")

    def decode_token(self, token: str) -> str:
        try:
            payload = jwt.decode(
                token,
                self.settings.app_secret_key,
                algorithms=["HS256"],
            )
        except jwt.PyJWTError as exc:
            raise AuthError("Invalid or expired token", code="invalid_token") from exc
        user_id = payload.get("sub")
        if not user_id:
            raise AuthError("Invalid token payload", code="invalid_token")
        return str(user_id)

    def register(self, email: str, password: str, display_name: str) -> tuple[Account, str]:
        if len(password) < 8:
            raise AuthError("Password must be at least 8 characters", code="weak_password")
        if not email.strip() or "@" not in email:
            raise AuthError("Valid email is required", code="invalid_email")
        if not display_name.strip():
            raise AuthError("Display name is required", code="invalid_name")
        try:
            account = self.store.create_account(
                email=email,
                password_hash=self.hash_password(password),
                display_name=display_name,
            )
        except ValueError as exc:
            if str(exc) == "email_already_registered":
                raise AuthError("Email already registered", code="email_taken") from exc
            raise
        return account, self.create_access_token(account.id)

    def login(self, email: str, password: str) -> tuple[Account, str]:
        record = self.store.get_by_email(email)
        if not record:
            raise AuthError("Invalid email or password", code="invalid_credentials")
        account, password_hash = record
        if not self.verify_password(password, password_hash):
            raise AuthError("Invalid email or password", code="invalid_credentials")
        return account, self.create_access_token(account.id)

    def get_account(self, user_id: str) -> Account:
        account = self.store.get_by_id(user_id)
        if not account:
            raise AuthError("Account not found", code="not_found")
        return account
