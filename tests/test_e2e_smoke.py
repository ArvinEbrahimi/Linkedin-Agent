"""In-process E2E smoke test — runs in CI without a live server or Groq key."""

from unittest.mock import AsyncMock, MagicMock

import chromadb
import pytest
from httpx import ASGITransport, AsyncClient
from langgraph.checkpoint.memory import MemorySaver

from app.agents.graph import build_graph
from app.agents.models import IntentClassification
from app.config import Settings
from app.main import create_app
from app.models.content import ContentPostLLMOutput, HookVariant
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


def _hook() -> HookVariant:
    return HookVariant(hook="Hook", style="bold", save_optimization_hint="saves")


def _alt() -> AlternativeOption:
    return AlternativeOption(title="A", content="B", comparison="C")


@pytest.fixture
def smoke_app(tmp_path):
    settings = Settings(
        groq_api_key="smoke-test-key",
        database_url=f"sqlite:///{(tmp_path / 'e2e.db').as_posix()}",
        chroma_persist_dir=str(tmp_path / "chroma"),
    )
    llm_settings = MagicMock()
    llm_settings.groq_model = "llama-3.3-70b-versatile"
    llm_settings.groq_api_key = "smoke-test-key"
    llm_settings.langfuse_enabled = False

    service = LLMService(settings, chat_model=MagicMock())

    async def structured_invoke(messages, schema):
        if schema is IntentClassification:
            return IntentClassification(intent="content", needs_clarification=False)
        if schema is LinkAidResponse:
            return LinkAidResponse(
                understanding="Smoke test request.",
                main_recommendation="Smoke test post content.",
                alternatives=[_alt()],
                strategic_reasoning="Algorithm alignment.",
                execution_tips="Post Tuesday morning.",
                follow_up_question="Want a carousel?",
            )
        if schema is ContentPostLLMOutput:
            return ContentPostLLMOutput(
                understanding="Post request.",
                full_post="Full smoke test post.",
                hooks=[_hook(), _hook(), _hook()],
                cta="Comment below.",
                hashtags=["#test"],
                first_comment="Link here.",
                alternative_angles=[_alt(), _alt()],
                strategic_reasoning="Proof wins.",
                execution_tips="Morning post.",
                follow_up_question="Carousel?",
            )
        return schema.model_validate({})

    service.structured_invoke = AsyncMock(side_effect=structured_invoke)

    memory = MemoryService(
        settings,
        chroma_client=chromadb.EphemeralClient(),
        embedding_function=HashEmbeddingFunction(),
    )
    content = ContentService(service)
    limiter = OutreachRateLimiter(str(tmp_path / "outreach.db"), daily_limit=20)
    networking = NetworkingService(service, limiter)
    profile = ProfileService(service)
    advisor = AdvisorService(service, memory)
    search = SearchService(settings)
    strategy = StrategyService(service, memory, search)

    graph = build_graph(
        service,
        content,
        networking,
        profile,
        memory,
        advisor,
        strategy,
        MemorySaver(),
    )

    app = create_app()
    app.state.graph = graph
    app.state.content_service = content
    app.state.networking_service = networking
    app.state.profile_service = profile
    app.state.memory_service = memory
    app.state.advisor_service = advisor
    app.state.strategy_service = strategy
    return app


@pytest.mark.asyncio
async def test_e2e_health_and_openapi(smoke_app):
    transport = ASGITransport(app=smoke_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        openapi = await client.get("/openapi.json")
        assert openapi.status_code == 200
        paths = openapi.json()["paths"]
        assert "/api/v1/chat" in paths
        assert "/api/v1/content/post" in paths


@pytest.mark.asyncio
async def test_e2e_chat_flow(smoke_app):
    transport = ASGITransport(app=smoke_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={
                "message": "Write a LinkedIn post about FastAPI",
                "thread_id": "e2e-ci",
                "user_id": "e2e-user",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "content"
    assert "main_recommendation" in data["response"]


@pytest.mark.asyncio
async def test_e2e_memory_profile_roundtrip(smoke_app):
    transport = ASGITransport(app=smoke_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        put = await client.put(
            "/api/v1/memory/profile/e2e-user",
            json={"profile": {"niche": "E2E testing", "goals": ["CI green"]}},
        )
        assert put.status_code == 200

        get = await client.get("/api/v1/memory/profile/e2e-user")
        assert get.status_code == 200
        assert get.json()["profile"]["niche"] == "E2E testing"
