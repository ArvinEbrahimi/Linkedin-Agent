import logging

from app.agents.state import LinkAidState
from app.services.content import ContentService, post_response_to_linkaid
from app.services.llm import LLMService

logger = logging.getLogger(__name__)


async def content_agent(
    state: LinkAidState,
    llm_service: LLMService,
    content_service: ContentService,
) -> dict:
    post_type = state.get("metadata", {}).get("post_type", "text")
    response = await content_service.generate_from_messages(
        state["messages"],
        state.get("user_context"),
        post_type=post_type,
    )
    linkaid = post_response_to_linkaid(response)

    return {
        "draft_response": linkaid.model_dump(),
        "metadata": {
            **state.get("metadata", {}),
            "intent": "content",
            "model": llm_service.settings.groq_model,
            "content_result": response.result.model_dump(),
        },
    }
