from typing import Literal

from pydantic import BaseModel, Field

from app.models.responses import LinkAidResponse

IntentType = Literal["content", "networking", "profile", "advisor", "strategy", "general"]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    thread_id: str = Field(default="default")
    user_id: str = Field(default="default")


class ChatResponse(BaseModel):
    thread_id: str
    intent: IntentType
    response: LinkAidResponse
