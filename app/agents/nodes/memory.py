import logging

from langchain_core.messages import SystemMessage

from app.agents.models import IntentClassification
from app.agents.state import LinkAidState
from app.services.advisor import AdvisorService
from app.services.llm import LLMService
from app.services.memory_store import MemoryService

logger = logging.getLogger(__name__)

CLASSIFY_SYSTEM = """You are an intent classifier for LinkAid,
a LinkedIn personal branding assistant.

Classify the user's message into exactly one intent:
- content: posts, carousels, video scripts, hooks, campaigns
- networking: connection requests, icebreakers, profile outreach
- profile: headline, about, experience, skills optimization, OR questions about
  how/where to improve their LinkedIn profile
- advisor: daily briefing, post performance, outreach plan
- strategy: personal narrative, competitors, content calendar
- general: greetings, thanks, mixed or unclear requests

Rules for needs_clarification:
- Set FALSE for greetings (سلام, hello, hi) → intent=general
- Set FALSE for profile improvement questions (e.g. "از کجا شروع کنم برای پروفایل",
  "how to improve my profile", "where should I start") → intent=profile
- Set FALSE when user context already includes niche, role, or goals
- Set TRUE only when the message is extremely vague AND no context exists
  (e.g. single word "help" with empty profile)

Provide clarification_question only when needs_clarification=true.
Match the user's language (Persian or English)."""


async def load_memory(state: LinkAidState, memory_service: MemoryService) -> dict:
    user_id = state.get("user_id", "default")
    thread_id = state.get("thread_id", "default")

    last_msg = state["messages"][-1] if state.get("messages") else None
    query = None
    if last_msg and hasattr(last_msg, "content"):
        query = str(last_msg.content)[:300]

    context = memory_service.get_user_context(user_id, query=query)
    summary = memory_service.get_thread_summary(user_id, thread_id)
    if summary:
        context["thread_summary"] = summary

    return {"user_context": context}


async def classify_intent(state: LinkAidState, llm_service: LLMService) -> dict:
    last_message = state["messages"][-1]
    context = state.get("user_context") or {}
    context_note = ""
    if context:
        context_note = f"\n\nKnown user context (use to avoid unnecessary clarification):\n{context}"

    classification = await llm_service.structured_invoke(
        [SystemMessage(content=CLASSIFY_SYSTEM + context_note), last_message],
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


async def save_memory(
    state: LinkAidState,
    memory_service: MemoryService,
    advisor_service: AdvisorService,
) -> dict:
    user_id = state.get("user_id", "default")
    thread_id = state.get("thread_id", "default")
    messages = state.get("messages", [])

    try:
        await advisor_service.update_thread_summary(user_id, thread_id, messages)
    except Exception:
        logger.exception("Failed to update thread summary")

    return {}
