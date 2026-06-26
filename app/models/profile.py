from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.responses import AlternativeOption

ProfileSection = Literal["headline", "about", "experience", "featured", "skills", "full"]
MAX_HEADLINE_CHARS = 220


class HeadlineVariant(BaseModel):
    headline: str
    keywords: list[str] = Field(default_factory=list)
    reasoning: str

    @field_validator("headline")
    @classmethod
    def validate_headline_length(cls, v: str) -> str:
        if len(v) > MAX_HEADLINE_CHARS:
            raise ValueError(f"Headline must be ≤{MAX_HEADLINE_CHARS} characters")
        return v


class ExperienceBullet(BaseModel):
    original: str | None = None
    rewritten: str
    metrics_used: str | None = None


class FeaturedItem(BaseModel):
    title: str
    description: str
    content_type: Literal["post", "link", "document", "project"] = "post"


class ProfileOptimizeRequest(BaseModel):
    section: ProfileSection
    current_content: str = Field(..., min_length=1, max_length=10000)
    role: str | None = Field(default=None, description="e.g. Senior Backend Engineer")
    years_experience: int | None = Field(default=None, ge=0)
    tech_stack: list[str] = Field(default_factory=list)
    target_goal: str | None = Field(default=None, description="jobs, leads, thought leadership")
    language: Literal["fa-en", "en"] = "fa-en"
    company: str | None = None
    role_title: str | None = None


class ProfileSectionResult(BaseModel):
    section: ProfileSection
    headlines: list[HeadlineVariant] | None = None
    about: str | None = None
    about_structure: str | None = None
    experience_bullets: list[ExperienceBullet] | None = None
    featured_items: list[FeaturedItem] | None = None
    top_skills: list[str] | None = None
    skills_to_add: list[str] | None = None


class ProfileOptimizeLLMOutput(BaseModel):
    understanding: str
    headlines: list[HeadlineVariant] | None = None
    about: str | None = None
    about_structure: str | None = None
    experience_bullets: list[ExperienceBullet] | None = None
    featured_items: list[FeaturedItem] | None = None
    top_skills: list[str] | None = None
    skills_to_add: list[str] | None = None
    alternative_angles: list[AlternativeOption] = Field(min_length=2, max_length=3)
    strategic_reasoning: str
    execution_tips: str
    follow_up_question: str


class ProfileOptimizeResponse(BaseModel):
    result: ProfileSectionResult
    understanding: str
    strategic_reasoning: str
    execution_tips: str
    alternatives: list[AlternativeOption]
    follow_up_question: str
