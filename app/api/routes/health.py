from fastapi import APIRouter

from app.config import get_settings
from app.models.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description=(
        "Returns service name, version, and environment. "
        "Use for load balancers and Docker healthchecks."
    ),
)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        app=settings.app_name,
        version=settings.app_version,
        env=settings.env,
    )
