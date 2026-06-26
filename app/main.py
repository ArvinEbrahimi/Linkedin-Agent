import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import __version__
from app.agents import get_content_service, get_networking_service, init_agent
from app.api.routes.chat import router as chat_router
from app.api.routes.content import router as content_router
from app.api.routes.health import router as health_router
from app.api.routes.networking import router as networking_router
from app.config import get_settings
from app.core.exceptions import LinkAidError
from app.core.logging import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings)
    logger.info("Starting %s v%s [%s]", settings.app_name, settings.app_version, settings.env)

    graph = init_agent(settings)
    app.state.graph = graph
    app.state.content_service = get_content_service()
    app.state.networking_service = get_networking_service()
    logger.info("Agent graph ready")

    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Personal AI assistant for LinkedIn personal branding. Suggest-only.",
        lifespan=lifespan,
    )

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(content_router, prefix="/api/v1")
    app.include_router(networking_router, prefix="/api/v1")

    @app.exception_handler(LinkAidError)
    async def linkaid_error_handler(_request: Request, exc: LinkAidError) -> JSONResponse:
        status_code = 400
        if exc.code == "not_found":
            status_code = 404
        elif exc.code == "rate_limit_exceeded":
            status_code = 429
        elif exc.code == "configuration_error":
            status_code = 500

        return JSONResponse(
            status_code=status_code,
            content={"error": exc.code, "message": exc.message},
        )

    return app


app = create_app()
