import logging

from fastapi import APIRouter, Depends

from app.api.deps import get_advisor_service
from app.models.advisor import (
    AdvisorResponse,
    BriefingRequest,
    OutreachListRequest,
    PostAnalysisRequest,
)
from app.services.advisor import AdvisorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advisor", tags=["advisor"])


@router.post("/briefing", response_model=AdvisorResponse)
async def morning_briefing(
    request: BriefingRequest,
    advisor_service: AdvisorService = Depends(get_advisor_service),
) -> AdvisorResponse:
    return await advisor_service.morning_briefing(request)


@router.post("/post-analysis", response_model=AdvisorResponse)
async def post_analysis(
    request: PostAnalysisRequest,
    advisor_service: AdvisorService = Depends(get_advisor_service),
) -> AdvisorResponse:
    return await advisor_service.analyze_post(request)


@router.post("/outreach", response_model=AdvisorResponse)
async def outreach_suggestions(
    request: OutreachListRequest,
    advisor_service: AdvisorService = Depends(get_advisor_service),
) -> AdvisorResponse:
    return await advisor_service.outreach_suggestions(request)
