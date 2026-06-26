from unittest.mock import AsyncMock, MagicMock

import chromadb
import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.main import create_app
from app.models.networking import SWOTAnalysis
from app.models.responses import AlternativeOption
from app.models.strategy import (
    CalendarLLMOutput,
    CalendarSlot,
    CompetitorComparisonRow,
    CompetitorLLMOutput,
    CompetitorProfile,
    NarrativeLLMOutput,
    PersonalNarrative,
    SearchResult,
)
from app.models.user import UserProfile
from app.services.llm import LLMService
from app.services.memory_store import HashEmbeddingFunction, MemoryService
from app.services.search import SearchService
from app.services.strategy import StrategyService, detect_strategy_mode


def _alt() -> AlternativeOption:
    return AlternativeOption(
        title="Bold angle",
        content="Lead with contrarian take",
        comparison="Higher saves",
    )


def _narrative() -> PersonalNarrative:
    return PersonalNarrative(
        positioning_statement="I help fintech teams ship LLM agents that pass compliance.",
        elevator_pitch=(
            "I'm a backend engineer specializing in production LLM systems for regulated fintech. "
            "I help teams go from prototype to audited deployment in weeks, not quarters."
        ),
        unique_value_proposition=(
            "Bridge between Iranian engineering talent and EU fintech compliance."
        ),
        target_audience_summary=(
            "CTOs and engineering leads at fintech startups hiring remote senior backend."
        ),
        tone_keywords=["practical", "credible", "warm"],
    )


def _sample_narrative_output() -> NarrativeLLMOutput:
    return NarrativeLLMOutput(
        understanding="You want a personal narrative for LinkedIn.",
        narrative=_narrative(),
        alternative_angles=[_alt(), _alt()],
        strategic_reasoning=(
            "Positioning around compliance niche differentiates in crowded AI space."
        ),
        execution_tips="Add positioning line to headline and first About paragraph.",
        follow_up_question="Want headline variants based on this narrative?",
    )


def _sample_competitor_output() -> CompetitorLLMOutput:
    return CompetitorLLMOutput(
        understanding="You want competitor differentiation.",
        competitors=[
            CompetitorProfile(
                name="Alice Dev",
                positioning="AI educator for beginners",
                content_themes=["tutorials", "tool roundups"],
                strengths=["Large following"],
                weaknesses=["Shallow technical depth"],
            )
        ],
        comparison_table=[
            CompetitorComparisonRow(
                competitor="Alice Dev",
                their_angle="Beginner-friendly AI tips",
                your_differentiation="Production LLM in regulated fintech",
                content_opportunity="Case studies with compliance constraints",
            )
        ],
        differentiated_angles=["Compliance-first LLM deploys", "Iranian remote talent angle"],
        your_swot=SWOTAnalysis(
            strengths=["Deep backend + LLM"],
            weaknesses=["Smaller audience"],
            opportunities=["Underserved fintech niche"],
            threats=["Generic AI content noise"],
        ),
        alternative_angles=[_alt(), _alt()],
        strategic_reasoning="Own the compliance-production niche they avoid.",
        execution_tips="Publish one case study carousel per month.",
        follow_up_question="Analyze a second competitor?",
    )


def _sample_calendar_output() -> CalendarLLMOutput:
    return CalendarLLMOutput(
        understanding="You want a 4-week content calendar.",
        monthly_theme="Production LLM lessons from fintech",
        slots=[
            CalendarSlot(
                week=1,
                day="Tuesday",
                post_type="text",
                theme="RAG eval pitfalls",
                hook_idea="Your RAG demo scores 95% — production users still hate it.",
                cta_hint="Comment your worst eval surprise",
            ),
            CalendarSlot(
                week=1,
                day="Thursday",
                post_type="carousel",
                theme="Compliance checklist for LLM features",
                hook_idea="5 questions legal will ask before you ship.",
                cta_hint="Save for your next sprint review",
            ),
            CalendarSlot(
                week=2,
                day="Tuesday",
                post_type="poll",
                theme="Team structure for AI features",
                hook_idea="Who owns prompt changes in your org?",
                cta_hint="Vote + explain in comments",
            ),
            CalendarSlot(
                week=2,
                day="Friday",
                post_type="document",
                theme="Architecture diagram walkthrough",
                hook_idea="How we cut LLM latency 40% without bigger GPUs.",
                cta_hint="Save the diagram template",
            ),
        ],
        alternative_angles=[_alt(), _alt()],
        strategic_reasoning="Mix formats to train algorithm on diverse engagement.",
        execution_tips="Batch-create carousels on weekends.",
        follow_up_question="Want full post drafts for week 1?",
    )


@pytest.fixture
def temp_settings(tmp_path):
    db_path = (tmp_path / "strategy_test.db").as_posix()
    return Settings(
        groq_api_key="test",
        database_url=f"sqlite:///{db_path}",
        chroma_persist_dir=str(tmp_path / "chroma"),
    )


@pytest.fixture
def memory_service(temp_settings):
    return MemoryService(
        temp_settings,
        chroma_client=chromadb.EphemeralClient(),
        embedding_function=HashEmbeddingFunction(),
    )


@pytest.fixture
def mock_search_service():
    service = MagicMock(spec=SearchService)
    service.search_competitors = AsyncMock(
        return_value=(
            [
                SearchResult(
                    title="Alice Dev on LinkedIn",
                    url="https://example.com/alice",
                    snippet="AI educator sharing weekly tutorials.",
                )
            ],
            "none",
        )
    )
    return service


@pytest.fixture
def mock_llm_service():
    settings = MagicMock()
    settings.groq_model = "llama-3.3-70b-versatile"
    settings.groq_api_key = "test-key"
    service = LLMService(settings, chat_model=MagicMock())

    async def structured_invoke(messages, schema):
        if schema is NarrativeLLMOutput:
            return _sample_narrative_output()
        if schema is CompetitorLLMOutput:
            return _sample_competitor_output()
        if schema is CalendarLLMOutput:
            return _sample_calendar_output()
        return schema.model_validate({})

    service.structured_invoke = AsyncMock(side_effect=structured_invoke)
    return service


@pytest.fixture
def strategy_service(mock_llm_service, memory_service, mock_search_service):
    return StrategyService(mock_llm_service, memory_service, mock_search_service)


def test_detect_strategy_mode():
    assert detect_strategy_mode("Analyze my competitors Alice and Bob") == "competitor"
    assert detect_strategy_mode("Build a 4-week content calendar") == "calendar"
    assert detect_strategy_mode("Help me with my personal narrative") == "narrative"


@pytest.mark.asyncio
async def test_narrative_uses_stored_niche(strategy_service, memory_service):
    from app.models.strategy import NarrativeRequest

    memory_service.save_profile(
        "user1",
        UserProfile(niche="LLM agents for fintech", goals=["thought leadership"]),
    )
    response = await strategy_service.build_narrative(NarrativeRequest(user_id="user1"))
    assert response.user_context_used.get("niche") == "LLM agents for fintech"
    assert response.narrative.positioning_statement


@pytest.mark.asyncio
async def test_competitor_returns_comparison_table(
    strategy_service, memory_service, mock_search_service
):
    from app.models.strategy import CompetitorRequest

    memory_service.save_profile(
        "user1",
        UserProfile(niche="Python backend", competitors=["Alice Dev"]),
    )
    response = await strategy_service.analyze_competitors(
        CompetitorRequest(user_id="user1", competitor_names=["Alice Dev"])
    )
    assert len(response.comparison_table) >= 1
    assert response.differentiated_angles
    mock_search_service.search_competitors.assert_awaited_once()


@pytest.mark.asyncio
async def test_calendar_returns_slots(strategy_service):
    from app.models.strategy import CalendarRequest

    response = await strategy_service.build_calendar(CalendarRequest(user_id="user1", weeks=4))
    assert response.weeks == 4
    assert len(response.slots) >= 4
    assert response.monthly_theme


@pytest.mark.asyncio
async def test_search_service_graceful_fallback_no_key():
    service = SearchService(Settings(groq_api_key="test", tavily_api_key=None))
    results, provider = await service.search("LinkedIn AI trends 2026", max_results=2)
    assert provider in ("duckduckgo", "none")
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_strategy_narrative_api(strategy_service, memory_service):
    memory_service.save_profile(
        "user1",
        UserProfile(niche="DevOps", goals=["consulting leads"]),
    )
    app = create_app()
    app.state.strategy_service = strategy_service
    app.state.memory_service = memory_service
    app.state.advisor_service = MagicMock()
    app.state.graph = MagicMock()
    app.state.content_service = MagicMock()
    app.state.networking_service = MagicMock()
    app.state.profile_service = MagicMock()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/strategy/narrative",
            json={"user_id": "user1"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["narrative"]["positioning_statement"]
    assert data["user_context_used"]["niche"] == "DevOps"


@pytest.mark.asyncio
async def test_strategy_competitor_api(strategy_service, memory_service):
    app = create_app()
    app.state.strategy_service = strategy_service
    app.state.memory_service = memory_service
    app.state.advisor_service = MagicMock()
    app.state.graph = MagicMock()
    app.state.content_service = MagicMock()
    app.state.networking_service = MagicMock()
    app.state.profile_service = MagicMock()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/strategy/competitor",
            json={"user_id": "user1", "competitor_names": ["Alice Dev", "Bob ML"]},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["comparison_table"]) >= 1
    assert data["differentiated_angles"]
