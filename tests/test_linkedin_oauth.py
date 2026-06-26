"""Tests for LinkedIn OAuth service."""

import pytest

from app.config import Settings
from app.core.exceptions import ConfigurationError
from app.services.linkedin_oauth import LinkedInOAuthService
from app.services.memory_store import MemoryService


@pytest.fixture
def oauth_service(tmp_path):
    settings = Settings(
        groq_api_key="test",
        database_url=f"sqlite:///{(tmp_path / 'oauth.db').as_posix()}",
        chroma_persist_dir=str(tmp_path / "chroma"),
        linkedin_client_id="test-client",
        linkedin_client_secret="test-secret",
    )
    memory = MemoryService(settings)
    return LinkedInOAuthService(settings, memory)


def test_auth_url_requires_config(tmp_path):
    settings = Settings(
        groq_api_key="test",
        database_url=f"sqlite:///{(tmp_path / 'x.db').as_posix()}",
        chroma_persist_dir=str(tmp_path / "chroma"),
    )
    memory = MemoryService(settings)
    service = LinkedInOAuthService(settings, memory)
    with pytest.raises(ConfigurationError):
        service.create_auth_url("user1")


def test_auth_url_and_status(oauth_service):
    url, state = oauth_service.create_auth_url("user-1")
    assert "linkedin.com/oauth" in url
    assert state
    assert "client_id=test-client" in url

    status = oauth_service.get_status("user-1")
    assert status["connected"] is False

    from app.models.linkedin import LinkedInUserInfo

    oauth_service._save_account(
        "user-1",
        {"access_token": "tok", "expires_in": 3600},
        LinkedInUserInfo(sub="li-123", name="Test User", email="t@example.com"),
    )
    oauth_service._merge_profile(
        "user-1",
        LinkedInUserInfo(sub="li-123", name="Test User", email="t@example.com"),
    )

    status = oauth_service.get_status("user-1")
    assert status["connected"] is True
    assert status["name"] == "Test User"

    profile = oauth_service.memory.get_profile("user-1")
    assert profile is not None
    assert profile.linkedin_sub == "li-123"
    assert profile.name == "Test User"
