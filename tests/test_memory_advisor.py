import uuid
from unittest.mock import AsyncMock, MagicMock

import chromadb
import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.main import create_app
from app.models.advisor import AdvisorLLMOutput, OutreachSuggestion
from app.models.responses import AlternativeOption
from app.models.user import PostRecord, UserProfile
from app.services.advisor import AdvisorService
from app.services.llm import LLMService
from app.services.memory_store import HashEmbeddingFunction, MemoryService


def _alt() -> AlternativeOption:
    return AlternativeOption(title="A", content="B", comparison="C")


def _sample_advisor_output() -> AdvisorLLMOutput:
    return AdvisorLLMOutput(
        understanding="Morning briefing for your LinkedIn day.",
        main_content=(
            "**Today's Focus:** Post about LLM agents in fintech.\n"
            "**Engagement:** Comment on 3 AI posts in first 60 min."
        ),
        outreach_suggestions=[
            OutreachSuggestion(
                target_description="Senior recruiter in AI",
                reason="Matches your job search goal",
                priority_score=0.9,
                suggested_action="Connect with personalized note",
            )
        ],
        alternative_angles=[_alt(), _alt()],
        strategic_reasoning="Saves-focused content aligns with 2026 algorithm.",
        execution_tips="Post at 9am Tehran time.",
        follow_up_question="Want a draft post for today's topic?",
    )


@pytest.fixture
def temp_settings(tmp_path):
    db_path = (tmp_path / "test.db").as_posix()
    return Settings(
        groq_api_key="test",
        database_url=f"sqlite:///{db_path}",
        chroma_persist_dir=str(tmp_path / "chroma"),
    )


@pytest.fixture
def memory_service(temp_settings):
    client = chromadb.EphemeralClient()
    ef = HashEmbeddingFunction()
    return MemoryService(temp_settings, chroma_client=client, embedding_function=ef)


@pytest.fixture
def mock_llm_service():
    settings = MagicMock()
    settings.groq_model = "llama-3.3-70b-versatile"
    settings.groq_api_key = "test-key"
    service = LLMService(settings, chat_model=MagicMock())

    async def structured_invoke(messages, schema):
        if schema is AdvisorLLMOutput:
            return _sample_advisor_output()
        if hasattr(schema, "__name__") and schema.__name__ == "ThreadSummaryOutput":
            from app.services.advisor import ThreadSummaryOutput

            return ThreadSummaryOutput(summary="User focuses on LLM agents in fintech.")
        return schema.model_validate({})

    service.structured_invoke = AsyncMock(side_effect=structured_invoke)
    return service


@pytest.fixture
def advisor_service(mock_llm_service, memory_service):
    return AdvisorService(mock_llm_service, memory_service)


def test_memory_save_and_recall_niche(memory_service):
    profile = UserProfile(
        user_id="user1",
        niche="LLM agents for fintech",
        goals=["remote job offers", "thought leadership"],
        competitors=["competitor-a"],
    )
    memory_service.save_profile("user1", profile)

    context = memory_service.get_user_context("user1")
    assert context["niche"] == "LLM agents for fintech"
    assert "remote job offers" in context["goals"]


def test_memory_posts_crud(memory_service):
    user_id = f"posts-{uuid.uuid4().hex[:8]}"
    post = PostRecord(content="My post about FastAPI performance", saves=42)
    memory_service.add_post(user_id, post)
    posts = memory_service.list_posts(user_id)
    assert len(posts) == 1
    assert posts[0].saves == 42
    assert posts[0].content == "My post about FastAPI performance"


def test_thread_summary_persistence(memory_service):
    memory_service.save_thread_summary("user1", "thread-1", "Discussed headline optimization.")
    summary = memory_service.get_thread_summary("user1", "thread-1")
    assert "headline" in summary


@pytest.mark.asyncio
async def test_briefing_uses_stored_goals(advisor_service, memory_service):
    memory_service.save_profile(
        "user1",
        UserProfile(niche="Python backend", goals=["remote EU jobs"]),
    )
    from app.models.advisor import BriefingRequest

    response = await advisor_service.morning_briefing(BriefingRequest(user_id="user1"))
    assert response.user_context_used.get("niche") == "Python backend"
    assert "remote EU jobs" in response.user_context_used.get("goals", [])
    assert response.main_content


@pytest.mark.asyncio
async def test_memory_profile_api(memory_service):
    app = create_app()
    app.state.memory_service = memory_service
    app.state.advisor_service = MagicMock()
    app.state.graph = MagicMock()
    app.state.content_service = MagicMock()
    app.state.networking_service = MagicMock()
    app.state.profile_service = MagicMock()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        put_resp = await client.put(
            "/api/v1/memory/profile/user1",
            json={
                "profile": {
                    "niche": "AI engineering",
                    "goals": ["lead generation"],
                }
            },
        )
        assert put_resp.status_code == 200

        get_resp = await client.get("/api/v1/memory/profile/user1")
        assert get_resp.status_code == 200
        assert get_resp.json()["profile"]["niche"] == "AI engineering"


@pytest.mark.asyncio
async def test_advisor_briefing_api(advisor_service, memory_service):
    memory_service.save_profile(
        "user1",
        UserProfile(niche="DevOps", goals=["consulting leads"]),
    )
    app = create_app()
    app.state.advisor_service = advisor_service
    app.state.memory_service = memory_service
    app.state.graph = MagicMock()
    app.state.content_service = MagicMock()
    app.state.networking_service = MagicMock()
    app.state.profile_service = MagicMock()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/advisor/briefing",
            json={"user_id": "user1"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "briefing"
    assert data["user_context_used"]["niche"] == "DevOps"
