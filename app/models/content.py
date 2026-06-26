from typing import Literal

from pydantic import BaseModel, Field

from app.models.responses import AlternativeOption

PostType = Literal["text", "carousel", "video", "poll", "document"]


class HookVariant(BaseModel):
    hook: str = Field(..., description="Opening hook line (first 1-2 sentences)")
    style: str = Field(..., description="e.g. bold-claim, story, question, contrarian")
    save_optimization_hint: str = Field(
        ..., description="Why this hook drives saves in 2026 algorithm"
    )


class ContentPostRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    post_type: PostType = "text"
    tone: str | None = Field(default=None, description="e.g. professional, warm, bold")
    language: Literal["fa-en", "en"] = "fa-en"


class ContentPostResult(BaseModel):
    topic: str
    post_type: PostType
    full_post: str
    hooks: list[HookVariant] = Field(min_length=3, max_length=3)
    cta: str
    hashtags: list[str] = Field(default_factory=list)
    first_comment: str = Field(
        ..., description="Suggested first comment (for external links)"
    )


class ContentPostResponse(BaseModel):
    result: ContentPostResult
    understanding: str
    strategic_reasoning: str
    execution_tips: str
    alternatives: list[AlternativeOption]
    follow_up_question: str


class ContentPostLLMOutput(BaseModel):
    understanding: str
    full_post: str
    hooks: list[HookVariant] = Field(min_length=3, max_length=3)
    cta: str
    hashtags: list[str] = Field(default_factory=list)
    first_comment: str
    alternative_angles: list[AlternativeOption] = Field(min_length=2, max_length=3)
    strategic_reasoning: str
    execution_tips: str
    follow_up_question: str


class CampaignDayIdea(BaseModel):
    day: int = Field(ge=1, le=30)
    theme: str
    post_type: PostType
    title: str
    hook_idea: str
    key_message: str


class ContentCampaignRequest(BaseModel):
    niche: str = Field(..., min_length=3, max_length=300)
    goal: str | None = Field(default=None, description="e.g. job offers, thought leadership")
    language: Literal["fa-en", "en"] = "fa-en"


class CampaignPlan(BaseModel):
    campaign_name: str
    niche: str
    weekly_themes: list[str] = Field(min_length=4, max_length=5)
    days: list[CampaignDayIdea] = Field(min_length=30, max_length=30)


class ContentCampaignResponse(BaseModel):
    plan: CampaignPlan
    strategic_reasoning: str
    execution_tips: str
    follow_up_question: str
