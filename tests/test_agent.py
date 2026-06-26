from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from app.agents.graph import build_graph
from app.agents.models import IntentClassification
from app.agents.nodes.respond import format_response
from app.agents.state import LinkAidState
from app.main import create_app
from app.models.responses import AlternativeOption, LinkAidResponse
from app.services.llm import LLMService


def _sample_response() -> LinkAidResponse:
    return LinkAidResponse(
        understanding="You want a LinkedIn post about Python backend engineering.",
        main_recommendation="Hook: I reduced API latency by 60% with one architectural change...",
        alternatives=[
            AlternativeOption(
                title="Story angle",
                content="Last quarter our team faced 2s response times...",
                comparison="Higher comment rate, more personal",
            )
        ],
        strategic_reasoning="Document carousels with proof points drive saves in 2026.",
        execution_tips="Post Tuesday 9am Tehran. Put GitHub link in first comment.",
        follow_up_question="What metric or achievement should we highlight?",
    )


@pytest.fixture
def mock_llm_service():
    settings = MagicMock()
    settings.groq_model = "llama-3.3-70b-versatile"
    settings.groq_api_key = "test-key"

    service = LLMService(settings, chat_model=MagicMock())

    async def structured_invoke(messages, schema):
        if schema is IntentClassification:
            return IntentClassification(intent="content", needs_clarification=False)
        if schema is LinkAidResponse:
            return _sample_response()
        return schema.model_validate({})

    service.structured_invoke = AsyncMock(side_effect=structured_invoke)
    service.build_system_prompt = MagicMock(return_value="system prompt")
    return service


@pytest.fixture
def graph(mock_llm_service):
    return build_graph(mock_llm_service, MemorySaver())


@pytest.mark.asyncio
async def test_graph_returns_valid_response(graph):
    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content="Write a LinkedIn post about FastAPI")],
            "user_id": "test",
            "thread_id": "test-thread",
            "intent": "general",
            "user_context": {},
            "draft_response": None,
            "needs_clarification": False,
            "clarification_question": None,
            "metadata": {},
        },
        config={"configurable": {"thread_id": "test-thread"}},
    )

    assert result["intent"] == "content"
    draft = LinkAidResponse.model_validate(result["draft_response"])
    assert draft.main_recommendation
    assert draft.follow_up_question


@pytest.mark.asyncio
async def test_format_response_clarification():
    state: LinkAidState = {
        "messages": [],
        "user_id": "u",
        "thread_id": "t",
        "intent": "general",
        "user_context": {},
        "draft_response": None,
        "needs_clarification": True,
        "clarification_question": "What is your target role?",
        "metadata": {},
    }
    result = await format_response(state)
    response = LinkAidResponse.model_validate(result["draft_response"])
    assert response.follow_up_question == "What is your target role?"
    assert len(response.alternatives) == 0


@pytest.mark.asyncio
async def test_chat_endpoint_with_mock_graph(mock_llm_service, graph):
    app = create_app()
    app.state.graph = graph

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={"message": "Write a post about AI agents", "thread_id": "t1"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == "t1"
    assert data["intent"] == "content"
    assert "main_recommendation" in data["response"]
    assert "follow_up_question" in data["response"]


@pytest.mark.asyncio
async def test_chat_endpoint_missing_api_key_returns_error():
    app = create_app()
    from app.agents.graph import build_graph
    from app.config import Settings

    settings = Settings(groq_api_key=None)
    service = LLMService(settings)
    app.state.graph = build_graph(service, MemorySaver())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={"message": "help me"},
        )

    assert response.status_code == 500
    assert response.json()["error"] == "configuration_error"
