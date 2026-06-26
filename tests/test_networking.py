import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.core.exceptions import RateLimitError
from app.main import create_app
from app.models.networking import (
    FollowUpStep,
    OutreachLLMOutput,
    OutreachRequest,
    ProfileAnalysisLLMOutput,
    ProfileAnalyzeRequest,
    SWOTAnalysis,
)
from app.models.responses import AlternativeOption
from app.services.llm import LLMService
from app.services.networking import NetworkingService, build_analyze_system_prompt
from app.services.rate_limit import OutreachRateLimiter


def _swot() -> SWOTAnalysis:
    return SWOTAnalysis(
        strengths=["Senior engineer at top company"],
        weaknesses=["High profile, may not respond"],
        opportunities=["Shared interest in AI"],
        threats=["Generic message will be ignored"],
    )


def _alt() -> AlternativeOption:
    return AlternativeOption(
        title="Comment first",
        content="Comment on their recent post before connecting",
        comparison="Higher acceptance rate",
    )


def _sample_analysis_output() -> ProfileAnalysisLLMOutput:
    return ProfileAnalysisLLMOutput(
        understanding="You want to connect with a senior ML engineer.",
        summary="Senior ML engineer at a FAANG company, active in AI content.",
        swot=_swot(),
        icebreakers=[
            "Loved your post on RAG pipelines",
            "Your point about eval frameworks resonated",
            "We both spoke at PyData last year",
        ],
        connection_request=(
            "Hi! Your RAG post was spot-on. I'm building similar systems — would love to connect."
        ),
        alternative_angles=[_alt(), _alt()],
        strategic_reasoning="Personalized notes referencing specific content win in 2026.",
        execution_tips="Comment on their latest post first. Send request Tuesday morning.",
        follow_up_question="Do you want an InMail version too?",
    )


def _sample_outreach_output() -> OutreachLLMOutput:
    return OutreachLLMOutput(
        understanding="You want a full outreach sequence.",
        connection_request=(
            "Hi! Your AI agents post was insightful. Building similar — would love to connect."
        ),
        follow_ups=[
            FollowUpStep(
                step=1,
                channel="connection_note",
                body="Just bumping this — would enjoy exchanging notes on agent architectures.",
                timing="5 days after request",
            ),
            FollowUpStep(
                step=2,
                channel="inmail",
                subject="Quick question on your agent framework",
                body="Hi, I noticed your work on multi-agent systems...",
                timing="1 week after step 1",
            ),
            FollowUpStep(
                step=3,
                channel="direct_message",
                body="No pressure — happy to share our eval framework if useful.",
                timing="1 week after step 2",
            ),
        ],
        alternative_angles=[_alt(), _alt()],
        strategic_reasoning="3-touch sequence without being pushy.",
        execution_tips="Max 20 requests/day. Engage with content first.",
        follow_up_question="Should we tailor for a recruiter vs engineer?",
        sensitive_flags=[],
    )


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name


@pytest.fixture
def rate_limiter(temp_db):
    return OutreachRateLimiter(temp_db, daily_limit=20)


@pytest.fixture
def mock_llm_service():
    settings = MagicMock()
    settings.groq_model = "llama-3.3-70b-versatile"
    settings.groq_api_key = "test-key"
    service = LLMService(settings, chat_model=MagicMock())

    async def structured_invoke(messages, schema):
        if schema is ProfileAnalysisLLMOutput:
            return _sample_analysis_output()
        if schema is OutreachLLMOutput:
            return _sample_outreach_output()
        return schema.model_validate({})

    service.structured_invoke = AsyncMock(side_effect=structured_invoke)
    return service


@pytest.fixture
def networking_service(mock_llm_service, rate_limiter):
    return NetworkingService(mock_llm_service, rate_limiter)


def test_connection_request_max_300_chars():
    long_msg = "x" * 301
    with pytest.raises(ValidationError):
        ProfileAnalysisLLMOutput(
            understanding="x",
            summary="x",
            swot=_swot(),
            icebreakers=["a", "b", "c"],
            connection_request=long_msg,
            alternative_angles=[_alt(), _alt()],
            strategic_reasoning="x",
            execution_tips="x",
            follow_up_question="x",
        )


def test_build_analyze_prompt_includes_context():
    prompt = build_analyze_system_prompt("Backend engineer seeking remote roles")
    assert "300" in prompt
    assert "Backend engineer" in prompt


@pytest.mark.asyncio
async def test_analyze_profile_returns_swot_and_connection(networking_service):
    response = await networking_service.analyze_profile(
        ProfileAnalyzeRequest(
            profile_text="Senior ML Engineer at Google. 10 years experience. Passionate about RAG.",
        )
    )
    assert response.result.swot.strengths
    assert len(response.result.icebreakers) >= 3
    assert len(response.result.connection_request) <= 300


@pytest.mark.asyncio
async def test_outreach_returns_3_step_sequence(networking_service):
    response = await networking_service.generate_outreach(
        OutreachRequest(profile_text="CTO at a fintech startup. Hiring backend engineers.")
    )
    assert len(response.sequence.follow_ups) == 3
    assert len(response.sequence.connection_request) <= 300
    assert response.daily_remaining == 19


@pytest.mark.asyncio
async def test_rate_limit_blocks_21st_request(networking_service, rate_limiter):
    user_id = "rate-test-user"
    rate_limiter.reset_user(user_id)

    for _ in range(20):
        await networking_service.generate_outreach(
            OutreachRequest(profile_text="Engineer at a startup with 5 years exp.", user_id=user_id)
        )

    with pytest.raises(RateLimitError):
        await networking_service.generate_outreach(
            OutreachRequest(profile_text="Another profile text here for testing.", user_id=user_id)
        )


@pytest.mark.asyncio
async def test_hitl_review_flag(networking_service, mock_llm_service):
    sensitive = _sample_outreach_output()
    sensitive.sensitive_flags = ["C-level executive"]

    async def invoke(messages, schema):
        return sensitive

    mock_llm_service.structured_invoke = AsyncMock(side_effect=invoke)

    response = await networking_service.generate_outreach(
        OutreachRequest(
            profile_text="CEO of a major tech company. 20 years leadership.",
            require_hitl_review=False,
        )
    )
    assert response.requires_review is True
    assert response.review_note


@pytest.mark.asyncio
async def test_networking_analyze_api(networking_service):
    app = create_app()
    app.state.networking_service = networking_service
    app.state.graph = MagicMock()
    app.state.content_service = MagicMock()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/networking/analyze",
            json={"profile_text": "Senior backend engineer at Digikala. Python, FastAPI."},
        )

    assert response.status_code == 200
    data = response.json()
    assert "swot" in data["result"]
    assert len(data["result"]["connection_request"]) <= 300


@pytest.mark.asyncio
async def test_networking_outreach_api_rate_limit(networking_service, rate_limiter):
    app = create_app()
    app.state.networking_service = networking_service
    app.state.graph = MagicMock()
    app.state.content_service = MagicMock()

    user_id = "api-rate-test"
    rate_limiter.reset_user(user_id)
    profile = "Product manager at a SaaS company with AI focus."

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(20):
            resp = await client.post(
                "/api/v1/networking/outreach",
                json={"profile_text": profile, "user_id": user_id},
            )
            assert resp.status_code == 200

        resp = await client.post(
            "/api/v1/networking/outreach",
            json={"profile_text": profile, "user_id": user_id},
        )
        assert resp.status_code == 429
