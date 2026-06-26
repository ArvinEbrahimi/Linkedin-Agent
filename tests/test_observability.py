"""Tests for LangFuse observability helpers."""

from app.config import Settings
from app.core.observability import build_run_config, create_langfuse_handler


def test_langfuse_disabled_without_keys():
    settings = Settings(groq_api_key="test")
    assert settings.langfuse_enabled is False
    assert create_langfuse_handler(settings) is None
    assert build_run_config(settings) == {}


def test_build_run_config_merges_overrides():
    settings = Settings(groq_api_key="test")
    config = build_run_config(
        settings,
        configurable={"thread_id": "t1"},
        metadata={"user_id": "u1"},
    )
    assert config["configurable"] == {"thread_id": "t1"}
    assert config["metadata"] == {"user_id": "u1"}
    assert "callbacks" not in config
