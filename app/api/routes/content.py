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


@router.post("/post", response_model=ContentPostResponse)
async def generate_post(
    request: ContentPostRequest,
    content_service: ContentService = Depends(get_content_service),
) -> ContentPostResponse:
    return await content_service.generate_post(request)


@router.post("/campaign", response_model=ContentCampaignResponse)
async def generate_campaign(
    request: ContentCampaignRequest,
    content_service: ContentService = Depends(get_content_service),
) -> ContentCampaignResponse:
    return await content_service.generate_campaign(request)
