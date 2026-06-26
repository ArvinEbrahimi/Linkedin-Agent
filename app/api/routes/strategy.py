import logging

from fastapi import APIRouter, Depends

from app.api.deps import get_strategy_service
from app.models.strategy import (
    CalendarRequest,
    CalendarResponse,
    CompetitorRequest,
    CompetitorResponse,
    NarrativeRequest,
    NarrativeResponse,
)
from app.services.strategy import StrategyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/strategy", tags=["strategy"])


@router.post(
    "/narrative",
    response_model=NarrativeResponse,
    summary="Build personal narrative",
    description="Positioning statement and elevator pitch for LinkedIn branding.",
)
async def personal_narrative(
    request: NarrativeRequest,
    strategy_service: StrategyService = Depends(get_strategy_service),
) -> NarrativeResponse:
    return await strategy_service.build_narrative(request)


@router.post(
    "/competitor",
    response_model=CompetitorResponse,
    summary="Competitor differentiation analysis",
    description="Comparison table, SWOT, and differentiated content angles with web search.",
)
async def competitor_analysis(
    request: CompetitorRequest,
    strategy_service: StrategyService = Depends(get_strategy_service),
) -> CompetitorResponse:
    return await strategy_service.analyze_competitors(request)


@router.post(
    "/calendar",
    response_model=CalendarResponse,
    summary="Content calendar",
    description="Multi-week calendar with post types, themes, hooks, and CTAs.",
)
async def content_calendar(
    request: CalendarRequest,
    strategy_service: StrategyService = Depends(get_strategy_service),
) -> CalendarResponse:
    return await strategy_service.build_calendar(request)
