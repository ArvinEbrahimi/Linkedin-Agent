from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.models.content import (
    CampaignDayIdea,
    CampaignPlan,
    ContentCampaignRequest,
    ContentPostLLMOutput,
    ContentPostRequest,
    HookVariant,
)
from app.models.responses import AlternativeOption
from app.services.content import (
    ContentService,
    build_campaign_system_prompt,
    build_post_system_prompt,
    load_content_prompt,
    post_response_to_linkaid,
)
from app.services.llm import LLMService


def _hook() -> HookVariant:
    return HookVariant(
        hook="90% of AI demos fail in production.",
        style="bold-claim",
        save_optimization_hint="Contrarian stats drive saves",
    )


def _sample_post_output() -> ContentPostLLMOutput:
    alt = AlternativeOption(
        title="Technical deep-dive",
        content="Walk through the architecture step by step...",
        comparison="Better for senior engineers, fewer likes but more saves",
    )
    return ContentPostLLMOutput(
        understanding="You want a LinkedIn post about FastAPI performance.",
        full_post="Last month I cut API latency by 60%...\n\nHere's how:",
        hooks=[_hook(), _hook(), _hook()],
        cta="Save this for your next project. Comment your stack.",
        hashtags=["#FastAPI", "#Python", "#Backend"],
        first_comment="GitHub repo link: https://example.com",
        alternative_angles=[alt, alt],
        strategic_reasoning="Personal proof + numbers drive saves in 2026.",
        execution_tips="Post Tuesday 9am Tehran. Engage in first 60 minutes.",
        follow_up_question="Should we add a carousel version?",
    )


def _sample_campaign() -> CampaignPlan:
    day = CampaignDayIdea(
        day=1,
        theme="Origin Story",
        post_type="text",
        title="Why I became a backend engineer",
        hook_idea="I almost quit programming in 2018...",
        key_message="Vulnerability builds trust",
    )
    return CampaignPlan(
        campaign_name="30 Days of Backend Excellence",
        niche="Python backend engineering",
        weekly_themes=["Origin", "Technical", "Lessons", "Community"],
        days=[day.model_copy(update={"day": i}) for i in range(1, 31)],
    )


@pytest.fixture
def mock_llm_service():
    settings = MagicMock()
    settings.groq_model = "llama-3.3-70b-versatile"
    settings.groq_api_key = "test-key"
    service = LLMService(settings, chat_model=MagicMock())

    async def structured_invoke(messages, schema):
        if schema is ContentPostLLMOutput:
            return _sample_post_output()
        if schema is CampaignPlan:
            return _sample_campaign()
        return schema.model_validate({})

    service.structured_invoke = AsyncMock(side_effect=structured_invoke)
    return service


@pytest.fixture
def content_service(mock_llm_service):
    return ContentService(mock_llm_service)


def test_load_content_prompts_exist():
    for post_type in ["text", "carousel", "video", "poll", "document"]:
        prompt = load_content_prompt(post_type)
        assert "2026" in prompt or "Hook" in prompt


def test_build_post_system_prompt_includes_topic():
    prompt = build_post_system_prompt("text", "FastAPI caching", "fa-en", "warm")
    assert "FastAPI caching" in prompt
    assert "text" in prompt.lower()


def test_build_campaign_system_prompt_includes_niche():
    prompt = build_campaign_system_prompt("LLM agents", "job offers", "fa-en")
    assert "LLM agents" in prompt
    assert "30" in prompt


@pytest.mark.asyncio
async def test_generate_post_returns_hooks_and_cta(content_service):
    response = await content_service.generate_post(
        ContentPostRequest(topic="FastAPI performance tips")
    )
    assert response.result.topic == "FastAPI performance tips"
    assert len(response.result.hooks) == 3
    assert response.result.cta
    assert response.result.full_post


@pytest.mark.asyncio
async def test_generate_campaign_returns_30_days(content_service):
    response = await content_service.generate_campaign(
        ContentCampaignRequest(niche="AI engineering")
    )
    assert len(response.plan.days) == 30
    assert len(response.plan.weekly_themes) >= 4


def test_post_response_to_linkaid_includes_hooks():
    from app.services.content import _to_post_response

    output = _sample_post_output()
    post_response = _to_post_response(output, "FastAPI", "text")
    linkaid = post_response_to_linkaid(post_response)
    assert "90% of AI demos" in linkaid.main_recommendation
    assert linkaid.follow_up_question


@pytest.mark.asyncio
async def test_content_post_api(content_service):
    app = create_app()
    app.state.content_service = content_service
    app.state.graph = MagicMock()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/content/post",
            json={"topic": "Building LangGraph agents", "post_type": "text"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["result"]["hooks"]) == 3
    assert data["result"]["cta"]
    assert data["result"]["full_post"]


@pytest.mark.asyncio
async def test_content_campaign_api(content_service):
    app = create_app()
    app.state.content_service = content_service
    app.state.graph = MagicMock()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/content/campaign",
            json={"niche": "DevOps for startups"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["plan"]["days"]) == 30
