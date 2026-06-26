import logging

from fastapi import APIRouter, Depends

from app.api.deps import get_networking_service
from app.models.networking import (
    OutreachRequest,
    OutreachResponse,
    ProfileAnalyzeRequest,
    ProfileAnalyzeResponse,
)
from app.services.networking import NetworkingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/networking", tags=["networking"])


@router.post("/analyze", response_model=ProfileAnalyzeResponse)
async def analyze_profile(
    request: ProfileAnalyzeRequest,
    networking_service: NetworkingService = Depends(get_networking_service),
) -> ProfileAnalyzeResponse:
    return await networking_service.analyze_profile(request)


@router.post("/outreach", response_model=OutreachResponse)
async def generate_outreach(
    request: OutreachRequest,
    networking_service: NetworkingService = Depends(get_networking_service),
) -> OutreachResponse:
    return await networking_service.generate_outreach(request)
