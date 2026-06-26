"""LangFuse observability — optional tracing for LLM and LangGraph runs."""

from __future__ import annotations

import logging
from typing import Any

from app.config import Settings

logger = logging.getLogger(__name__)

_langfuse_client: Any | None = None


def create_langfuse_handler(settings: Settings) -> Any | None:
    """Return a LangChain callback handler when LangFuse keys are configured."""
    if not settings.langfuse_enabled:
        return None

    try:
        from langfuse.langchain import CallbackHandler
    except ImportError:
        logger.warning("langfuse package not installed — tracing disabled")
        return None

    return CallbackHandler(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )


def init_langfuse(settings: Settings) -> Any | None:
    """Initialize LangFuse client for flush on shutdown."""
    global _langfuse_client
    if not settings.langfuse_enabled:
        return None

    try:
        from langfuse import Langfuse
    except ImportError:
        logger.warning("langfuse package not installed — tracing disabled")
        return None

    _langfuse_client = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
    logger.info("LangFuse tracing enabled host=%s", settings.langfuse_host)
    return _langfuse_client


def shutdown_langfuse() -> None:
    global _langfuse_client
    if _langfuse_client is not None:
        try:
            _langfuse_client.flush()
        except Exception:
            logger.exception("LangFuse flush failed")
        _langfuse_client = None


def build_run_config(settings: Settings, **overrides: Any) -> dict[str, Any]:
    """Build LangGraph / LangChain runnable config with optional LangFuse callbacks."""
    config: dict[str, Any] = {}
    handler = create_langfuse_handler(settings)
    if handler is not None:
        config["callbacks"] = [handler]
    config.update(overrides)
    return config
