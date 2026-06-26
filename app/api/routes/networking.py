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


@router.post(
    "/analyze",
    response_model=ProfileAnalyzeResponse,
    summary="Analyze a LinkedIn profile",
    description="SWOT analysis, icebreakers, and a connection request draft (≤300 chars).",
)
async def analyze_profile(
    request: ProfileAnalyzeRequest,
    networking_service: NetworkingService = Depends(get_networking_service),
) -> ProfileAnalyzeResponse:
    return await networking_service.analyze_profile(request)


@router.post(
    "/outreach",
    response_model=OutreachResponse,
    summary="Generate outreach sequence",
    description="3-step outreach sequence with optional HITL review flag. Rate-limited to 20/day.",
)
async def generate_outreach(
    request: OutreachRequest,
    networking_service: NetworkingService = Depends(get_networking_service),
) -> OutreachResponse:
    return await networking_service.generate_outreach(request)
