from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    thread_id: str = Field(default="default")
    user_id: str = Field(default="default")


class ChatResponse(BaseModel):
    thread_id: str
    response: dict
