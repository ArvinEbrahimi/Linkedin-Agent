from typing import Literal

from pydantic import BaseModel, Field

from app.models.content import PostType
from app.models.networking import SWOTAnalysis
from app.models.responses import AlternativeOption

StrategyMode = Literal["narrative", "competitor", "calendar"]


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class PersonalNarrative(BaseModel):
    positioning_statement: str = Field(
        ..., description="One-line positioning for LinkedIn headline/about"
    )
    elevator_pitch: str = Field(..., description="30-second spoken pitch (3-4 sentences)")
    unique_value_proposition: str
    target_audience_summary: str
    tone_keywords: list[str] = Field(min_length=2, max_length=5)


class NarrativeRequest(BaseModel):
    user_id: str = "default"
    background: str | None = Field(
        default=None, description="Extra career context beyond stored profile"
    )
    target_audience: str | None = None


class NarrativeLLMOutput(BaseModel):
    understanding: str
    narrative: PersonalNarrative
    alternative_angles: list[AlternativeOption] = Field(min_length=2, max_length=3)
    strategic_reasoning: str
    execution_tips: str
    follow_up_question: str


class NarrativeResponse(BaseModel):
    narrative: PersonalNarrative
    understanding: str
    strategic_reasoning: str
    execution_tips: str
    alternatives: list[AlternativeOption]
    follow_up_question: str
    user_context_used: dict = Field(default_factory=dict)


class CompetitorProfile(BaseModel):
    name: str
    positioning: str
    content_themes: list[str] = Field(min_length=1, max_length=5)
    strengths: list[str] = Field(min_length=1, max_length=4)
    weaknesses: list[str] = Field(min_length=1, max_length=4)


class CompetitorComparisonRow(BaseModel):
    competitor: str
    their_angle: str
    your_differentiation: str
    content_opportunity: str


class CompetitorRequest(BaseModel):
    user_id: str = "default"
    competitor_names: list[str] = Field(min_length=1, max_length=5)
    your_niche: str | None = None


class CompetitorLLMOutput(BaseModel):
    understanding: str
    competitors: list[CompetitorProfile] = Field(min_length=1)
    comparison_table: list[CompetitorComparisonRow] = Field(min_length=1)
    differentiated_angles: list[str] = Field(min_length=2, max_length=6)
    your_swot: SWOTAnalysis
    alternative_angles: list[AlternativeOption] = Field(min_length=2, max_length=3)
    strategic_reasoning: str
    execution_tips: str
    follow_up_question: str


class CompetitorResponse(BaseModel):
    competitors: list[CompetitorProfile]
    comparison_table: list[CompetitorComparisonRow]
    differentiated_angles: list[str]
    your_swot: SWOTAnalysis
    understanding: str
    strategic_reasoning: str
    execution_tips: str
    alternatives: list[AlternativeOption]
    follow_up_question: str
    search_sources_used: list[str] = Field(default_factory=list)
    user_context_used: dict = Field(default_factory=dict)


class CalendarSlot(BaseModel):
    week: int = Field(ge=1, le=8)
    day: str = Field(..., description="Weekday name, e.g. Tuesday")
    post_type: PostType
    theme: str
    hook_idea: str
    cta_hint: str


class CalendarRequest(BaseModel):
    user_id: str = "default"
    weeks: int = Field(default=4, ge=1, le=8)
    posting_frequency: str | None = Field(
        default=None, description="e.g. 3/week — overrides stored profile"
    )
    focus_themes: list[str] | None = Field(
        default=None, description="Optional themes to weave into the calendar"
    )


class CalendarLLMOutput(BaseModel):
    understanding: str
    monthly_theme: str
    slots: list[CalendarSlot] = Field(min_length=4)
    alternative_angles: list[AlternativeOption] = Field(min_length=2, max_length=3)
    strategic_reasoning: str
    execution_tips: str
    follow_up_question: str


class CalendarResponse(BaseModel):
    weeks: int
    monthly_theme: str
    slots: list[CalendarSlot]
    understanding: str
    strategic_reasoning: str
    execution_tips: str
    alternatives: list[AlternativeOption]
    follow_up_question: str
    user_context_used: dict = Field(default_factory=dict)
