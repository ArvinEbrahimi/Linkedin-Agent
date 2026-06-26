import logging

from langchain_core.messages import SystemMessage

from app.agents.models import IntentClassification
from app.agents.state import LinkAidState
from app.services.llm import LLMService

logger = logging.getLogger(__name__)

CLASSIFY_SYSTEM = """You are an intent classifier for LinkAid,
a LinkedIn personal branding assistant.

Classify the user's message into exactly one intent:
- content: posts, carousels, video scripts, hooks, campaigns
- networking: connection requests, icebreakers, profile outreach
- profile: headline, about, experience, skills optimization
- advisor: daily briefing, post performance, outreach plan
- strategy: personal narrative, competitors, content calendar
- general: anything else or mixed requests

Set needs_clarification=true only when the message is too vague to help
(e.g. "help me with LinkedIn" with no context). Provide a specific
clarification_question in Persian or English matching the user's language."""


async def load_memory(state: LinkAidState) -> dict:
    return {"user_context": state.get("user_context") or {}}


async def classify_intent(state: LinkAidState, llm_service: LLMService) -> dict:
    last_message = state["messages"][-1]
    classification = await llm_service.structured_invoke(
        [SystemMessage(content=CLASSIFY_SYSTEM), last_message],
        IntentClassification,
    )
    logger.info(
        "Classified intent=%s needs_clarification=%s",
        classification.intent,
        classification.needs_clarification,
    )
    return {
        "intent": classification.intent,
        "needs_clarification": classification.needs_clarification,
        "clarification_question": classification.clarification_question,
    }


async def save_memory(_state: LinkAidState) -> dict:
    return {}
