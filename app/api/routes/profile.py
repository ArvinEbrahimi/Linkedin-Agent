import logging

from fastapi import APIRouter, Depends

from app.api.deps import get_profile_service
from app.models.profile import ProfileOptimizeRequest, ProfileOptimizeResponse
from app.services.profile import ProfileService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post(
    "/optimize",
    response_model=ProfileOptimizeResponse,
    summary="Optimize a profile section",
    description="Rewrite headline (3 variants ≤220 chars), about, experience, featured, or skills.",
)
async def optimize_profile(
    request: ProfileOptimizeRequest,
    profile_service: ProfileService = Depends(get_profile_service),
) -> ProfileOptimizeResponse:
    return await profile_service.optimize(request)
