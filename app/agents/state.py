from typing import Annotated, Literal

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

IntentType = Literal["content", "networking", "profile", "advisor", "strategy", "general"]


class LinkAidState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    thread_id: str
    intent: IntentType
    user_context: dict
    draft_response: dict | None
    needs_clarification: bool
    clarification_question: str | None
    metadata: dict
