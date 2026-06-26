import logging

from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage

from app.api.deps import get_graph
from app.core.exceptions import ConfigurationError
from app.models.requests import ChatRequest, ChatResponse
from app.models.responses import LinkAidResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, graph=Depends(get_graph)) -> ChatResponse:
    config = {"configurable": {"thread_id": request.thread_id}}

    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "user_id": request.user_id,
        "thread_id": request.thread_id,
        "intent": "general",
        "user_context": {},
        "draft_response": None,
        "needs_clarification": False,
        "clarification_question": None,
        "metadata": {},
    }

    try:
        result = await graph.ainvoke(initial_state, config)
    except ConfigurationError:
        raise
    except Exception as exc:
        logger.exception("Graph invocation failed")
        raise ConfigurationError(f"Agent error: {exc}") from exc

    draft = result.get("draft_response")
    if not draft:
        raise ConfigurationError("Agent returned empty response")

    response = LinkAidResponse.model_validate(draft)
    intent = result.get("intent", "general")

    return ChatResponse(
        thread_id=request.thread_id,
        intent=intent,
        response=response,
    )
