import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app import __version__
from app.agents import (
    get_advisor_service,
    get_content_service,
    get_linkedin_service,
    get_memory_service,
    get_networking_service,
    get_profile_service,
    get_strategy_service,
    init_agent,
)
from app.agents.graph import checkpoint_db_path
from app.api.deps import attach_account_middleware
from app.api.openapi import API_DESCRIPTION, OPENAPI_TAGS
from app.api.routes.advisor import router as advisor_router
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.content import router as content_router
from app.api.routes.health import router as health_router
from app.api.routes.linkedin import router as linkedin_router
from app.api.routes.memory import router as memory_router
from app.api.routes.networking import router as networking_router
from app.api.routes.profile import router as profile_router
from app.api.routes.ready import router as ready_router
from app.api.routes.strategy import router as strategy_router
from app.config import get_settings
from app.core.exceptions import LinkAidError
from app.core.logging import setup_logging
from app.core.observability import init_langfuse, shutdown_langfuse
from app.services.auth import AuthError, AuthService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings)
    logger.info("Starting %s v%s [%s]", settings.app_name, settings.app_version, settings.env)

    if not settings.groq_configured:
        logger.warning("GROQ_API_KEY not set — /chat and AI endpoints will fail until configured")

    init_langfuse(settings)
    app.state.auth_service = AuthService(settings)

    db_path = checkpoint_db_path(settings.checkpoint_db_path)
    async with AsyncSqliteSaver.from_conn_string(db_path) as checkpointer:
        graph = init_agent(settings, checkpointer)
        app.state.graph = graph
        app.state.content_service = get_content_service()
        app.state.networking_service = get_networking_service()
        app.state.profile_service = get_profile_service()
        app.state.memory_service = get_memory_service()
        app.state.advisor_service = get_advisor_service()
        app.state.strategy_service = get_strategy_service()
        app.state.linkedin_service = get_linkedin_service()
        logger.info("Agent graph ready (async checkpointer)")

        yield

    shutdown_langfuse()
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=API_DESCRIPTION,
        lifespan=lifespan,
        openapi_tags=OPENAPI_TAGS,
        contact={"name": "LinkAid", "url": "https://github.com/ArvinEbrahimi/Linkedin-Agent"},
        license_info={"name": "Proprietary"},
    )

    app.middleware("http")(attach_account_middleware)

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(ready_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(content_router, prefix="/api/v1")
    app.include_router(networking_router, prefix="/api/v1")
    app.include_router(profile_router, prefix="/api/v1")
    app.include_router(memory_router, prefix="/api/v1")
    app.include_router(advisor_router, prefix="/api/v1")
    app.include_router(strategy_router, prefix="/api/v1")
    app.include_router(linkedin_router, prefix="/api/v1")

    @app.exception_handler(LinkAidError)
    async def linkaid_error_handler(_request: Request, exc: LinkAidError) -> JSONResponse:
        status_code = 400
        if exc.code == "not_found":
            status_code = 404
        elif exc.code == "rate_limit_exceeded":
            status_code = 429
        elif exc.code == "configuration_error":
            status_code = 500
        elif exc.code == "linkedin_oauth_error":
            status_code = 400
        elif exc.code in ("invalid_credentials", "invalid_token", "auth_error"):
            status_code = 401
        elif exc.code == "email_taken":
            status_code = 409
        elif exc.code == "weak_password":
            status_code = 422

        return JSONResponse(
            status_code=status_code,
            content={"error": exc.code, "message": exc.message},
        )

    return app


app = create_app()
