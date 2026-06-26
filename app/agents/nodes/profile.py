import logging

from app.agents.state import LinkAidState
from app.models.profile import ProfileSection
from app.services.llm import LLMService
from app.services.profile import ProfileService, profile_to_linkaid

logger = logging.getLogger(__name__)


async def profile_agent(
    state: LinkAidState,
    llm_service: LLMService,
    profile_service: ProfileService,
) -> dict:
    section: ProfileSection = state.get("metadata", {}).get("profile_section", "headline")
    response = await profile_service.optimize_from_messages(
        state["messages"],
        state.get("user_context"),
        section=section,
    )
    linkaid = profile_to_linkaid(response)

    return {
        "draft_response": linkaid.model_dump(),
        "metadata": {
            **state.get("metadata", {}),
            "intent": "profile",
            "model": llm_service.settings.groq_model,
            "profile_result": response.result.model_dump(),
        },
    }
