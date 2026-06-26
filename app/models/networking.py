from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.responses import AlternativeOption

MAX_CONNECTION_CHARS = 300


class SWOTAnalysis(BaseModel):
    strengths: list[str] = Field(min_length=1, max_length=5)
    weaknesses: list[str] = Field(min_length=1, max_length=5)
    opportunities: list[str] = Field(min_length=1, max_length=5)
    threats: list[str] = Field(min_length=1, max_length=5)


class FollowUpStep(BaseModel):
    step: int = Field(ge=1, le=3)
    channel: Literal["connection_note", "inmail", "direct_message"]
    subject: str | None = Field(default=None, description="InMail subject line")
    body: str
    timing: str = Field(..., description="When to send relative to previous step")


class ProfileAnalyzeRequest(BaseModel):
    profile_text: str = Field(..., min_length=20, max_length=10000)
    user_id: str = Field(default="default")
    your_context: str | None = Field(
        default=None, description="Your role/goal for personalization"
    )


class OutreachRequest(BaseModel):
    profile_text: str = Field(..., min_length=20, max_length=10000)
    user_id: str = Field(default="default")
    your_context: str | None = None
    require_hitl_review: bool = Field(
        default=False,
        description="Flag outreach for human review before copying",
    )


class ProfileAnalysisResult(BaseModel):
    summary: str
    swot: SWOTAnalysis
    icebreakers: list[str] = Field(min_length=3, max_length=5)
    connection_request: str = Field(..., max_length=MAX_CONNECTION_CHARS)

    @field_validator("connection_request")
    @classmethod
    def validate_connection_length(cls, v: str) -> str:
        if len(v) > MAX_CONNECTION_CHARS:
            raise ValueError(f"Connection request must be ≤{MAX_CONNECTION_CHARS} characters")
        return v


class OutreachSequence(BaseModel):
    connection_request: str = Field(..., max_length=MAX_CONNECTION_CHARS)
    follow_ups: list[FollowUpStep] = Field(min_length=3, max_length=3)

    @field_validator("connection_request")
    @classmethod
    def validate_connection_length(cls, v: str) -> str:
        if len(v) > MAX_CONNECTION_CHARS:
            raise ValueError(f"Connection request must be ≤{MAX_CONNECTION_CHARS} characters")
        return v


class ProfileAnalysisLLMOutput(BaseModel):
    understanding: str
    summary: str
    swot: SWOTAnalysis
    icebreakers: list[str] = Field(min_length=3, max_length=5)
    connection_request: str
    alternative_angles: list[AlternativeOption] = Field(min_length=2, max_length=3)
    strategic_reasoning: str
    execution_tips: str
    follow_up_question: str

    @field_validator("connection_request")
    @classmethod
    def validate_connection_length(cls, v: str) -> str:
        if len(v) > MAX_CONNECTION_CHARS:
            raise ValueError(f"Connection request must be ≤{MAX_CONNECTION_CHARS} characters")
        return v


class OutreachLLMOutput(BaseModel):
    understanding: str
    connection_request: str
    follow_ups: list[FollowUpStep] = Field(min_length=3, max_length=3)
    inmail_subject: str | None = None
    alternative_angles: list[AlternativeOption] = Field(min_length=2, max_length=3)
    strategic_reasoning: str
    execution_tips: str
    follow_up_question: str
    sensitive_flags: list[str] = Field(
        default_factory=list,
        description="Reasons this outreach needs careful review",
    )

    @field_validator("connection_request")
    @classmethod
    def validate_connection_length(cls, v: str) -> str:
        if len(v) > MAX_CONNECTION_CHARS:
            raise ValueError(f"Connection request must be ≤{MAX_CONNECTION_CHARS} characters")
        return v


class ProfileAnalyzeResponse(BaseModel):
    result: ProfileAnalysisResult
    understanding: str
    strategic_reasoning: str
    execution_tips: str
    alternatives: list[AlternativeOption]
    follow_up_question: str


class OutreachResponse(BaseModel):
    sequence: OutreachSequence
    understanding: str
    strategic_reasoning: str
    execution_tips: str
    alternatives: list[AlternativeOption]
    follow_up_question: str
    requires_review: bool = False
    review_note: str | None = None
    daily_remaining: int | None = None
