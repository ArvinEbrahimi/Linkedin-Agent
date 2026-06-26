import logging

from app.agents.state import LinkAidState
from app.services.llm import LLMService
from app.services.profile import (
    ProfileService,
    _infer_profile_section,
    _is_profile_advisory,
    _profile_baseline_from_context,
    profile_to_linkaid,
)

logger = logging.getLogger(__name__)


async def profile_agent(
    state: LinkAidState,
    llm_service: LLMService,
    profile_service: ProfileService,
) -> dict:
    last = state["messages"][-1]
    content = last.content if isinstance(last.content, str) else str(last.content)
    ctx = state.get("user_context") or {}

    if _is_profile_advisory(content):
        linkaid = await profile_service.advise_from_messages(state["messages"], ctx)
        return {
            "draft_response": linkaid.model_dump(),
            "metadata": {
                **state.get("metadata", {}),
                "intent": "profile",
                "profile_mode": "advisory",
                "model": llm_service.settings.groq_model,
            },
        }

    section = state.get("metadata", {}).get("profile_section") or _infer_profile_section(content)
    baseline = _profile_baseline_from_context(ctx)
    current_content = content
    if section == "full" and baseline and len(content) < 200:
        current_content = f"{baseline}\n\nUser request: {content}"

    response = await profile_service.optimize_from_messages(
        state["messages"],
        ctx,
        section=section,
        current_content=current_content,
    )
    linkaid = profile_to_linkaid(response)

    return {
        "draft_response": linkaid.model_dump(),
        "metadata": {
            **state.get("metadata", {}),
            "intent": "profile",
            "profile_mode": "optimize",
            "model": llm_service.settings.groq_model,
            "profile_result": response.result.model_dump(),
        },
    }
