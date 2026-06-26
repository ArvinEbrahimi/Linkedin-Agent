from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PostRecord(BaseModel):
    content: str
    post_type: Literal["text", "carousel", "video", "poll", "document"] = "text"
    posted_at: datetime | None = None
    impressions: int | None = None
    likes: int | None = None
    comments: int | None = None
    saves: int | None = None


class UserConstraints(BaseModel):
    iranian_market: bool = True
    max_daily_connections: int = Field(default=20, ge=1, le=20)
    no_video: bool = False
    bandwidth_limited: bool = False


class UserProfile(BaseModel):
    user_id: str = Field(default="default")
    linkedin_sub: str | None = None
    linkedin_headline: str | None = None
    linkedin_profile_url: str | None = None
    email: str | None = None
    about_summary: str | None = None
    name: str | None = None
    role: Literal["Backend", "FullStack", "AI Engineer"] | None = None
    years_experience: int | None = Field(default=None, ge=0)
    tech_stack: list[str] = Field(default_factory=list)
    niche: str | None = None
    target_audience: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    tone_preference: Literal["professional", "warm", "bold"] = "professional"
    language_mix: Literal["fa-en", "en"] = "fa-en"
    posting_frequency: str = "2-5/week"
    past_posts: list[PostRecord] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    constraints: UserConstraints = Field(default_factory=UserConstraints)
