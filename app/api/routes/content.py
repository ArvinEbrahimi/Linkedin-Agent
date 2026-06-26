import logging

from fastapi import APIRouter, Depends

from app.api.deps import get_content_service
from app.models.content import (
    ContentCampaignRequest,
    ContentCampaignResponse,
    ContentPostRequest,
    ContentPostResponse,
)
from app.services.content import ContentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["content"])


@router.post(
    "/post",
    response_model=ContentPostResponse,
    summary="Generate a LinkedIn post",
    description=(
        "Create a full post with 3 hook variants, CTA, hashtags, and first-comment suggestion."
    ),
)
async def generate_post(
    request: ContentPostRequest,
    content_service: ContentService = Depends(get_content_service),
) -> ContentPostResponse:
    return await content_service.generate_post(request)


@router.post(
    "/campaign",
    response_model=ContentCampaignResponse,
    summary="Generate a 30-day content campaign",
    description="Build a month-long campaign plan with daily themes, post types, and hook ideas.",
)
async def generate_campaign(
    request: ContentCampaignRequest,
    content_service: ContentService = Depends(get_content_service),
) -> ContentCampaignResponse:
    return await content_service.generate_campaign(request)
