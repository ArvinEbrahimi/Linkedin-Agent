from typing import Literal

from pydantic import BaseModel, Field

IntentType = Literal["content", "networking", "profile", "advisor", "strategy", "general"]


class IntentClassification(BaseModel):
    intent: IntentType = Field(
        description="Primary intent of the user message"
    )
    needs_clarification: bool = Field(
        default=False,
        description="True if the message is too vague to give a useful recommendation",
    )
    clarification_question: str | None = Field(
        default=None,
        description="Question to ask when needs_clarification is true",
    )
