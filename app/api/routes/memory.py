import logging

from fastapi import APIRouter, Depends

from app.api.deps import get_memory_service
from app.models.advisor import (
    MemoryPostsResponse,
    MemoryProfileResponse,
    PostMemoryRequest,
    ProfileMemoryRequest,
)
from app.services.memory_store import MemoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get(
    "/profile/{user_id}",
    response_model=MemoryProfileResponse,
    summary="Get stored user profile",
)
async def get_profile(
    user_id: str,
    memory_service: MemoryService = Depends(get_memory_service),
) -> MemoryProfileResponse:
    profile = memory_service.get_profile(user_id)
    return MemoryProfileResponse(user_id=user_id, profile=profile)


@router.put(
    "/profile/{user_id}",
    response_model=MemoryProfileResponse,
    summary="Save user profile",
    description="Persist niche, goals, competitors, and preferences for cross-session memory.",
)
async def save_profile(
    user_id: str,
    body: ProfileMemoryRequest,
    memory_service: MemoryService = Depends(get_memory_service),
) -> MemoryProfileResponse:
    profile = memory_service.save_profile(user_id, body.profile)
    return MemoryProfileResponse(user_id=user_id, profile=profile)


@router.get("/posts/{user_id}", response_model=MemoryPostsResponse, summary="List saved posts")
async def list_posts(
    user_id: str,
    memory_service: MemoryService = Depends(get_memory_service),
) -> MemoryPostsResponse:
    posts = memory_service.list_posts(user_id)
    return MemoryPostsResponse(user_id=user_id, posts=posts)


@router.post("/posts/{user_id}", response_model=MemoryPostsResponse, summary="Add a post record")
async def add_post(
    user_id: str,
    body: PostMemoryRequest,
    memory_service: MemoryService = Depends(get_memory_service),
) -> MemoryPostsResponse:
    memory_service.add_post(user_id, body.post)
    posts = memory_service.list_posts(user_id)
    return MemoryPostsResponse(user_id=user_id, posts=posts)
