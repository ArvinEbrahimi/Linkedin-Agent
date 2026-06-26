"""Auth service tests."""

import pytest

from app.config import Settings
from app.services.auth import AuthError, AuthService
from app.services.auth_store import AuthStore


@pytest.fixture
def auth_service(tmp_path):
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'auth.db').as_posix()}",
        app_secret_key="test-secret-key",
    )
    store = AuthStore(settings)
    return AuthService(settings, store)


def test_register_and_login(auth_service: AuthService):
    account, token = auth_service.register(
        "user@example.com", "securepass1", "Test User"
    )
    assert account.email == "user@example.com"
    assert token

    user_id = auth_service.decode_token(token)
    assert user_id == account.id

    logged_in, login_token = auth_service.login("user@example.com", "securepass1")
    assert logged_in.id == account.id
    assert login_token


def test_register_duplicate_email(auth_service: AuthService):
    auth_service.register("dup@example.com", "securepass1", "One")
    with pytest.raises(AuthError) as exc:
        auth_service.register("dup@example.com", "securepass2", "Two")
    assert exc.value.code == "email_taken"
