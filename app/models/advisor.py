from pydantic import BaseModel, Field

from app.models.responses import AlternativeOption
from app.models.user import PostRecord, UserProfile


class ProfileMemoryRequest(BaseModel):
    profile: UserProfile


class PostMemoryRequest(BaseModel):
    post: PostRecord


class MemoryProfileResponse(BaseModel):
    user_id: str
    profile: UserProfile | None


class MemoryPostsResponse(BaseModel):
    user_id: str
    posts: list[PostRecord]


class OutreachSuggestion(BaseModel):
    target_description: str
    reason: str
    priority_score: float = Field(ge=0.0, le=1.0)
    suggested_action: str


class BriefingRequest(BaseModel):
    user_id: str = "default"


class PostAnalysisRequest(BaseModel):
    user_id: str = "default"
    post_content: str = Field(..., min_length=10)
    impressions: int | None = Field(default=None, ge=0)
    likes: int | None = Field(default=None, ge=0)
    comments: int | None = Field(default=None, ge=0)
    saves: int | None = Field(default=None, ge=0)


class OutreachListRequest(BaseModel):
    user_id: str = "default"
    max_suggestions: int = Field(default=20, ge=1, le=20)


class AdvisorLLMOutput(BaseModel):
    understanding: str
    main_content: str
    outreach_suggestions: list[OutreachSuggestion] = Field(default_factory=list)
    alternative_angles: list[AlternativeOption] = Field(min_length=2, max_length=3)
    strategic_reasoning: str
    execution_tips: str
    follow_up_question: str


class AdvisorResponse(BaseModel):
    mode: str
    understanding: str
    main_content: str
    outreach_suggestions: list[OutreachSuggestion] = Field(default_factory=list)
    strategic_reasoning: str
    execution_tips: str
    alternatives: list[AlternativeOption]
    follow_up_question: str
    user_context_used: dict = Field(default_factory=dict)
