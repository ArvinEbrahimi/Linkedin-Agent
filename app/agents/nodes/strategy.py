import logging

from app.agents.state import LinkAidState
from app.models.strategy import StrategyMode
from app.services.llm import LLMService
from app.services.strategy import (
    StrategyService,
    calendar_to_linkaid,
    competitor_to_linkaid,
    detect_strategy_mode,
    narrative_to_linkaid,
)

logger = logging.getLogger(__name__)

_CONVERTERS = {
    "narrative": narrative_to_linkaid,
    "competitor": competitor_to_linkaid,
    "calendar": calendar_to_linkaid,
}


async def strategy_agent(
    state: LinkAidState,
    llm_service: LLMService,
    strategy_service: StrategyService,
) -> dict:
    mode: StrategyMode | str = state.get("metadata", {}).get("strategy_mode", "auto")
    if mode == "auto":
        last = state["messages"][-1]
        text = last.content if isinstance(last.content, str) else str(last.content)
        mode = detect_strategy_mode(text)

    response = await strategy_service.strategize_from_messages(
        state["messages"],
        state.get("user_id", "default"),
        mode=mode,
    )

    converter = _CONVERTERS.get(mode, narrative_to_linkaid)
    linkaid = converter(response)  # type: ignore[arg-type]

    return {
        "draft_response": linkaid.model_dump(),
        "metadata": {
            **state.get("metadata", {}),
            "intent": "strategy",
            "model": llm_service.settings.groq_model,
            "strategy_mode": mode,
            "user_context_used": getattr(response, "user_context_used", {}),
        },
    }
