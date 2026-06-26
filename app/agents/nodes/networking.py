import logging

from app.agents.state import LinkAidState
from app.services.llm import LLMService
from app.services.networking import NetworkingService, analysis_to_linkaid

logger = logging.getLogger(__name__)


async def networking_agent(
    state: LinkAidState,
    llm_service: LLMService,
    networking_service: NetworkingService,
) -> dict:
    response = await networking_service.analyze_from_messages(
        state["messages"],
        state.get("user_context"),
    )
    linkaid = analysis_to_linkaid(response)

    return {
        "draft_response": linkaid.model_dump(),
        "metadata": {
            **state.get("metadata", {}),
            "intent": "networking",
            "model": llm_service.settings.groq_model,
            "networking_result": response.result.model_dump(),
            "hitl_pending": False,
        },
    }
