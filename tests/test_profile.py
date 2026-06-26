from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.main import create_app
from app.models.profile import (
    HeadlineVariant,
    ProfileOptimizeLLMOutput,
    ProfileOptimizeRequest,
)
from app.models.responses import AlternativeOption
from app.services.llm import LLMService
from app.services.profile import ProfileService, build_profile_system_prompt


def _alt() -> AlternativeOption:
    return AlternativeOption(title="A", content="B", comparison="C")


def _headlines() -> list[HeadlineVariant]:
    return [
        HeadlineVariant(
            headline="Senior Backend Engineer | Python & FastAPI | Remote",
            keywords=["Python", "FastAPI", "Backend"],
            reasoning="Keyword-rich for recruiter search",
        ),
        HeadlineVariant(
            headline="I build scalable APIs for 1M+ users | Python | Open to remote",
            keywords=["API", "Python", "Remote"],
            reasoning="Value-prop first hook",
        ),
        HeadlineVariant(
            headline="Backend Engineer @ FinTech | 8yr exp | LLM & Microservices",
            keywords=["Backend", "FinTech", "LLM"],
            reasoning="Niche + experience signal",
        ),
    ]


def _sample_headline_output() -> ProfileOptimizeLLMOutput:
    return ProfileOptimizeLLMOutput(
        understanding="You want to optimize your LinkedIn headline.",
        headlines=_headlines(),
        alternative_angles=[_alt(), _alt()],
        strategic_reasoning="Headlines with metrics and keywords rank higher in 2026 search.",
        execution_tips="A/B test headline for 2 weeks. Track profile views.",
        follow_up_question="Should we optimize your About section next?",
    )


def _sample_about_output() -> ProfileOptimizeLLMOutput:
    return ProfileOptimizeLLMOutput(
        understanding="You want to rewrite your About section.",
        about=(
            "**Problem:** Teams struggle with slow APIs...\n\n"
            "**Proof:** I reduced latency 60%...\n\n"
            "**CTA:** DM me for a free architecture review."
        ),
        about_structure="Lines 1-3: Problem | Lines 4-8: Proof | Lines 9-10: CTA",
        alternative_angles=[_alt(), _alt()],
        strategic_reasoning="Problem-Proof-CTA drives profile-to-DM conversion.",
        execution_tips="First 2 lines visible before see-more — make them count.",
        follow_up_question="Want experience bullets optimized too?",
    )


@pytest.fixture
def mock_llm_service():
    settings = MagicMock()
    settings.groq_model = "llama-3.3-70b-versatile"
    settings.groq_api_key = "test-key"
    service = LLMService(settings, chat_model=MagicMock())

    async def structured_invoke(messages, schema):
        if schema is ProfileOptimizeLLMOutput:
            return _sample_headline_output()
        return schema.model_validate({})

    service.structured_invoke = AsyncMock(side_effect=structured_invoke)
    return service


@pytest.fixture
def profile_service(mock_llm_service):
    return ProfileService(mock_llm_service)


def test_headline_max_220_chars():
    with pytest.raises(ValidationError):
        HeadlineVariant(
            headline="x" * 221,
            keywords=["a"],
            reasoning="too long",
        )


def test_build_profile_prompt_includes_role():
    prompt = build_profile_system_prompt(
        ProfileOptimizeRequest(
            section="headline",
            current_content="Backend Developer",
            role="Senior Backend Engineer",
        )
    )
    assert "220" in prompt
    assert "Senior Backend Engineer" in prompt


@pytest.mark.asyncio
async def test_optimize_headline_returns_3_variants(profile_service):
    response = await profile_service.optimize(
        ProfileOptimizeRequest(
            section="headline",
            current_content="Backend Developer at a startup",
            role="Senior Backend Engineer",
        )
    )
    assert response.result.headlines is not None
    assert len(response.result.headlines) == 3
    for h in response.result.headlines:
        assert len(h.headline) <= 220
        assert h.reasoning


@pytest.mark.asyncio
async def test_optimize_about_section(mock_llm_service):
    async def invoke(messages, schema):
        return _sample_about_output()

    mock_llm_service.structured_invoke = AsyncMock(side_effect=invoke)
    service = ProfileService(mock_llm_service)

    response = await service.optimize(
        ProfileOptimizeRequest(
            section="about",
            current_content="I am a software engineer with experience in Python.",
        )
    )
    assert response.result.about
    assert "Problem" in response.result.about or "problem" in response.result.about.lower()


@pytest.mark.asyncio
async def test_profile_optimize_api(profile_service):
    app = create_app()
    app.state.profile_service = profile_service
    app.state.graph = MagicMock()
    app.state.content_service = MagicMock()
    app.state.networking_service = MagicMock()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/profile/optimize",
            json={
                "section": "headline",
                "current_content": "Software Engineer",
                "role": "Senior Backend Engineer",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["result"]["headlines"]) == 3
    assert data["strategic_reasoning"]
