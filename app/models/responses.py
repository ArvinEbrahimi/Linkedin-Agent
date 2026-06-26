from typing import Literal

from pydantic import BaseModel, Field


class AlternativeOption(BaseModel):
    title: str = Field(..., description="Short label for this alternative")
    content: str = Field(..., description="Ready-to-copy alternative suggestion")
    comparison: str = Field(
        ..., description="Brief comparison vs main recommendation"
    )


class LinkAidResponse(BaseModel):
    """Standard 6-section agent response structure."""

    understanding: str = Field(..., description="1-2 lines showing request comprehension")
    main_recommendation: str = Field(..., description="Primary ready-to-copy recommendation")
    alternatives: list[AlternativeOption] = Field(
        default_factory=list,
        min_length=0,
        max_length=3,
        description="2-3 alternative options with comparison",
    )
    strategic_reasoning: str = Field(
        ..., description="Why this works with 2026 LinkedIn algorithm"
    )
    execution_tips: str = Field(
        ..., description="Timing, length, interaction type, risk warnings"
    )
    follow_up_question: str = Field(
        ..., description="Question to gather more context"
    )


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    app: str
    version: str
    env: str
