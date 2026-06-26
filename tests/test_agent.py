from unittest.mock import AsyncMock, MagicMock

import chromadb
import pytest
from httpx import ASGITransport, AsyncClient
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from app.agents.graph import build_graph
from app.agents.models import IntentClassification
from app.agents.nodes.respond import format_response
from app.agents.state import LinkAidState
from app.config import Settings
from app.main import create_app
from app.models.content import ContentPostLLMOutput, HookVariant
from app.models.networking import ProfileAnalysisLLMOutput
from app.models.responses import AlternativeOption, LinkAidResponse
from app.services.advisor import AdvisorService
from app.services.content import ContentService
from app.services.llm import LLMService
from app.services.memory_store import HashEmbeddingFunction, MemoryService
from app.services.networking import NetworkingService
from app.services.profile import ProfileService
from app.services.rate_limit import OutreachRateLimiter
from app.services.search import SearchService
from app.services.strategy import StrategyService


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


def _sample_content_output() -> ContentPostLLMOutput:
    hook = HookVariant(
        hook="90% of backend tutorials skip this step.",
        style="bold-claim",
        save_optimization_hint="Gap-filling hooks drive saves",
    )
    alt = AlternativeOption(
        title="Story angle",
        content="Last quarter our team faced 2s response times...",
        comparison="Higher comment rate",
    )
    return ContentPostLLMOutput(
        understanding="You want a post about FastAPI.",
        full_post="Here is the full post about FastAPI performance...",
        hooks=[hook, hook, hook],
        cta="Save this. Comment your stack.",
        hashtags=["#FastAPI"],
        first_comment="Repo link in comment",
        alternative_angles=[alt, alt],
        strategic_reasoning="Proof-driven posts win in 2026.",
        execution_tips="Post Tuesday morning.",
        follow_up_question="Carousel version?",
    )


@pytest.fixture
def mock_llm_service():
    settings = MagicMock()
    settings.groq_model = "llama-3.3-70b-versatile"
    settings.groq_api_key = "test-key"

    service = LLMService(settings, chat_model=MagicMock())

    async def structured_invoke(messages, schema):
        if schema is IntentClassification:
            text = str(messages[-1].content).lower() if messages else ""
            if "competitor" in text or "calendar" in text or "narrative" in text:
                return IntentClassification(intent="strategy", needs_clarification=False)
            return IntentClassification(intent="content", needs_clarification=False)
        if schema is LinkAidResponse:
            return _sample_response()
        if schema is ContentPostLLMOutput:
            return _sample_content_output()
        if schema is ProfileAnalysisLLMOutput:
            return _sample_networking_output()
        from app.models.networking import SWOTAnalysis
        from app.models.strategy import (
            CalendarLLMOutput,
            CalendarSlot,
            CompetitorComparisonRow,
            CompetitorLLMOutput,
            CompetitorProfile,
            NarrativeLLMOutput,
            PersonalNarrative,
        )

        if schema is NarrativeLLMOutput:
            alt = AlternativeOption(title="A", content="B", comparison="C")
            return NarrativeLLMOutput(
                understanding="Narrative request.",
                narrative=PersonalNarrative(
                    positioning_statement="LLM engineer for fintech teams.",
                    elevator_pitch="I build production LLM systems for regulated industries.",
                    unique_value_proposition="Compliance + speed.",
                    target_audience_summary="Fintech CTOs.",
                    tone_keywords=["practical", "warm"],
                ),
                alternative_angles=[alt, alt],
                strategic_reasoning="Niche positioning wins.",
                execution_tips="Update About section.",
                follow_up_question="Headline variants?",
            )
        if schema is CompetitorLLMOutput:
            alt = AlternativeOption(title="A", content="B", comparison="C")
            return CompetitorLLMOutput(
                understanding="Competitor request.",
                competitors=[
                    CompetitorProfile(
                        name="Peer",
                        positioning="AI tips",
                        content_themes=["tutorials"],
                        strengths=["Audience"],
                        weaknesses=["Depth"],
                    )
                ],
                comparison_table=[
                    CompetitorComparisonRow(
                        competitor="Peer",
                        their_angle="Beginner tips",
                        your_differentiation="Production depth",
                        content_opportunity="Case studies",
                    )
                ],
                differentiated_angles=["Production LLM", "Compliance angle"],
                your_swot=SWOTAnalysis(
                    strengths=["Depth"],
                    weaknesses=["Reach"],
                    opportunities=["Niche"],
                    threats=["Noise"],
                ),
                alternative_angles=[alt, alt],
                strategic_reasoning="Differentiate on depth.",
                execution_tips="Weekly case study.",
                follow_up_question="More competitors?",
            )
        if schema is CalendarLLMOutput:
            alt = AlternativeOption(title="A", content="B", comparison="C")
            return CalendarLLMOutput(
                understanding="Calendar request.",
                monthly_theme="LLM production lessons",
                slots=[
                    CalendarSlot(
                        week=1,
                        day="Tuesday",
                        post_type="text",
                        theme="Eval pitfalls",
                        hook_idea="Your demo scores 95% — users still complain.",
                        cta_hint="Comment your surprise",
                    ),
                    CalendarSlot(
                        week=1,
                        day="Thursday",
                        post_type="carousel",
                        theme="Compliance",
                        hook_idea="5 legal questions before ship.",
                        cta_hint="Save this",
                    ),
                    CalendarSlot(
                        week=2,
                        day="Tuesday",
                        post_type="poll",
                        theme="Team ownership",
                        hook_idea="Who owns prompts?",
                        cta_hint="Vote",
                    ),
                    CalendarSlot(
                        week=2,
                        day="Friday",
                        post_type="document",
                        theme="Architecture",
                        hook_idea="Cut latency 40%.",
                        cta_hint="Save diagram",
                    ),
                ],
                alternative_angles=[alt, alt],
                strategic_reasoning="Mixed formats.",
                execution_tips="Batch on weekends.",
                follow_up_question="Draft week 1?",
            )
        return schema.model_validate({})

    service.structured_invoke = AsyncMock(side_effect=structured_invoke)
    service.build_system_prompt = MagicMock(return_value="system prompt")
    return service


def _sample_networking_output() -> ProfileAnalysisLLMOutput:
    from app.models.networking import SWOTAnalysis

    swot = SWOTAnalysis(
        strengths=["Active poster"],
        weaknesses=["Busy schedule"],
        opportunities=["Shared tech stack"],
        threats=["Generic approach"],
    )
    alt = AlternativeOption(title="A", content="B", comparison="C")
    return ProfileAnalysisLLMOutput(
        understanding="Networking request.",
        summary="Senior engineer at a tech company.",
        swot=swot,
        icebreakers=["ice1", "ice2", "ice3"],
        connection_request=(
            "Hi! Loved your post on Python — would love to connect and exchange ideas."
        ),
        alternative_angles=[alt, alt],
        strategic_reasoning="Personalized wins.",
        execution_tips="Comment first.",
        follow_up_question="InMail too?",
    )


@pytest.fixture
def content_service(mock_llm_service):
    return ContentService(mock_llm_service)


@pytest.fixture
def rate_limiter(tmp_path):
    return OutreachRateLimiter(str(tmp_path / "outreach.db"), daily_limit=20)


@pytest.fixture
def networking_service(mock_llm_service, rate_limiter):
    return NetworkingService(mock_llm_service, rate_limiter)


@pytest.fixture
def profile_service(mock_llm_service):
    return ProfileService(mock_llm_service)


@pytest.fixture
def memory_service(tmp_path):
    settings = Settings(
        groq_api_key="test",
        database_url=f"sqlite:///{(tmp_path / 'agent_test.db').as_posix()}",
        chroma_persist_dir=str(tmp_path / "chroma"),
    )
    return MemoryService(
        settings,
        chroma_client=chromadb.EphemeralClient(),
        embedding_function=HashEmbeddingFunction(),
    )


@pytest.fixture
def advisor_service(mock_llm_service, memory_service):
    return AdvisorService(mock_llm_service, memory_service)


@pytest.fixture
def strategy_service(mock_llm_service, memory_service):
    search = MagicMock(spec=SearchService)
    search.search_competitors = AsyncMock(return_value=([], "none"))
    return StrategyService(mock_llm_service, memory_service, search)


@pytest.fixture
def graph(
    mock_llm_service,
    content_service,
    networking_service,
    profile_service,
    memory_service,
    advisor_service,
    strategy_service,
):
    return build_graph(
        mock_llm_service,
        content_service,
        networking_service,
        profile_service,
        memory_service,
        advisor_service,
        strategy_service,
        MemorySaver(),
    )


@pytest.mark.asyncio
async def test_graph_routes_content_intent_to_content_agent(graph):
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
    assert "content_result" in result.get("metadata", {})
    draft = LinkAidResponse.model_validate(result["draft_response"])
    assert "FastAPI" in draft.main_recommendation or "90%" in draft.main_recommendation


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
async def test_graph_routes_strategy_intent_to_strategy_agent(graph):
    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content="Help me build my personal narrative on LinkedIn")],
            "user_id": "test",
            "thread_id": "test-strategy",
            "intent": "general",
            "user_context": {},
            "draft_response": None,
            "needs_clarification": False,
            "clarification_question": None,
            "metadata": {},
        },
        config={"configurable": {"thread_id": "test-strategy"}},
    )

    assert result["intent"] == "strategy"
    assert result.get("metadata", {}).get("strategy_mode") == "narrative"
    draft = LinkAidResponse.model_validate(result["draft_response"])
    assert "Positioning" in draft.main_recommendation


@pytest.mark.asyncio
async def test_chat_endpoint_with_mock_graph(
    mock_llm_service,
    content_service,
    networking_service,
    profile_service,
    memory_service,
    advisor_service,
    strategy_service,
    graph,
):
    app = create_app()
    app.state.graph = graph
    app.state.content_service = content_service
    app.state.networking_service = networking_service
    app.state.profile_service = profile_service
    app.state.memory_service = memory_service
    app.state.advisor_service = advisor_service
    app.state.strategy_service = strategy_service

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


@pytest.mark.asyncio
async def test_chat_endpoint_missing_api_key_returns_error(tmp_path):
    app = create_app()
    from app.agents.graph import build_graph
    from app.config import Settings

    settings = Settings(
        groq_api_key=None,
        database_url=f"sqlite:///{(tmp_path / 'missing_key.db').as_posix()}",
        chroma_persist_dir=str(tmp_path / "chroma"),
    )
    service = LLMService(settings)
    content = ContentService(service)
    limiter = OutreachRateLimiter(str(tmp_path / "outreach.db"), daily_limit=20)
    networking = NetworkingService(service, limiter)
    profile = ProfileService(service)
    memory = MemoryService(
        settings,
        chroma_client=chromadb.EphemeralClient(),
        embedding_function=HashEmbeddingFunction(),
    )
    advisor = AdvisorService(service, memory)
    search = SearchService(settings)
    strategy = StrategyService(service, memory, search)
    app.state.graph = build_graph(
        service, content, networking, profile, memory, advisor, strategy, MemorySaver()
    )
    app.state.content_service = content
    app.state.networking_service = networking
    app.state.profile_service = profile
    app.state.memory_service = memory
    app.state.advisor_service = advisor
    app.state.strategy_service = strategy

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={"message": "help me"},
        )

    assert response.status_code == 500
    assert response.json()["error"] == "configuration_error"
