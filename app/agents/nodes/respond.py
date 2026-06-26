import logging

from app.agents.state import LinkAidState
from app.models.responses import LinkAidResponse
from app.services.llm import LLMService

logger = logging.getLogger(__name__)


async def generate_response(state: LinkAidState, llm_service: LLMService) -> dict:
    from langchain_core.messages import SystemMessage

    intent = state.get("intent", "general")
    system_prompt = llm_service.build_system_prompt(intent, state.get("user_context"))

    if state.get("needs_clarification"):
        question = state.get("clarification_question") or (
            "هدف اصلی‌تان در لینکدین و حوزه تخصصی‌تان چیست؟"
        )
        system_prompt += (
            "\n\nThe user's message is somewhat vague. Still provide a genuinely helpful "
            f"recommendation using any available context. End with this follow-up question: {question}"
        )
    elif intent == "general":
        system_prompt += (
            "\n\nFor greetings or casual openers, respond warmly and suggest 2-3 concrete "
            "next steps they can take with LinkAid (profile, content, networking)."
        )

    response = await llm_service.structured_invoke(
        [SystemMessage(content=system_prompt), *state["messages"]],
        LinkAidResponse,
    )

    return {
        "draft_response": response.model_dump(),
        "metadata": {
            **state.get("metadata", {}),
            "intent": intent,
            "model": llm_service.settings.groq_model,
        },
    }


async def format_response(state: LinkAidState) -> dict:
    if state.get("needs_clarification") and not state.get("draft_response"):
        question = state.get("clarification_question") or (
            "لطفاً هدف اصلی‌تان از LinkedIn و حوزه تخصصی‌تان را بگویید."
        )
        draft = LinkAidResponse(
            understanding="درخواست شما کلی است و برای پیشنهاد دقیق به جزئیات بیشتری نیاز دارم.",
            main_recommendation="لطفاً ابتدا به سوال پایین پاسخ دهید تا پیشنهاد شخصی‌سازی‌شده بدهم.",
            alternatives=[],
            strategic_reasoning=(
                "الگوریتم ۲۰۲۶ محتوای niche-specific را ترجیح می‌دهد؛ "
                "context بیشتر = پیشنهاد هدفمندتر = engagement بالاتر."
            ),
            execution_tips="هرچه جزئیات بیشتری بدهید (نقش، حوزه، هدف)، خروجی عملی‌تر خواهد بود.",
            follow_up_question=question,
        )
        return {"draft_response": draft.model_dump()}

    draft = state.get("draft_response")
    if not draft:
        logger.error("format_response called without draft_response")
        raise ValueError("No draft_response to format")

    validated = LinkAidResponse.model_validate(draft)
    return {"draft_response": validated.model_dump()}
