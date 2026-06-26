import logging

from app.agents.state import LinkAidState
from app.services.advisor import AdvisorService, advisor_to_linkaid
from app.services.llm import LLMService

logger = logging.getLogger(__name__)


async def advisor_agent(
    state: LinkAidState,
    llm_service: LLMService,
    advisor_service: AdvisorService,
) -> dict:
    mode = state.get("metadata", {}).get("advisor_mode", "briefing")
    response = await advisor_service.advise_from_messages(
        state["messages"],
        state.get("user_id", "default"),
        mode=mode,
    )
    linkaid = advisor_to_linkaid(response)

    return {
        "draft_response": linkaid.model_dump(),
        "metadata": {
            **state.get("metadata", {}),
            "intent": "advisor",
            "model": llm_service.settings.groq_model,
            "advisor_mode": mode,
            "user_context_used": response.user_context_used,
        },
    }
