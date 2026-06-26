import logging
from pathlib import Path

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.models.content import (
    CampaignPlan,
    ContentCampaignRequest,
    ContentCampaignResponse,
    ContentPostLLMOutput,
    ContentPostRequest,
    ContentPostResponse,
    ContentPostResult,
    PostType,
)
from app.models.responses import LinkAidResponse
from app.services.llm import LLMService, load_base_prompt

logger = logging.getLogger(__name__)

CONTENT_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "agents" / "prompts" / "content"

POST_TYPES: list[PostType] = ["text", "carousel", "video", "poll", "document"]


def load_content_prompt(post_type: PostType) -> str:
    path = CONTENT_PROMPTS_DIR / f"{post_type}.md"
    if not path.exists():
        path = CONTENT_PROMPTS_DIR / "text.md"
    return path.read_text(encoding="utf-8")


def load_campaign_prompt() -> str:
    return (CONTENT_PROMPTS_DIR / "campaign.md").read_text(encoding="utf-8")


def build_post_system_prompt(
    post_type: PostType,
    topic: str,
    language: str,
    tone: str | None,
    user_context: dict | None = None,
) -> str:
    base = load_base_prompt()
    template = load_content_prompt(post_type)
    tone_line = f"Tone: {tone}" if tone else "Tone: professional, warm"
    lang_line = (
        "Language: Natural Persian + technical English terms"
        if language == "fa-en"
        else "Language: English"
    )
    context_block = f"\nUser context: {user_context}" if user_context else ""
    return (
        f"{base}\n\n## Content Task\n{template}\n\n"
        f"## Parameters\n"
        f"Topic: {topic}\n"
        f"Post type: {post_type}\n"
        f"{tone_line}\n"
        f"{lang_line}"
        f"{context_block}"
    )


def build_campaign_system_prompt(
    niche: str,
    goal: str | None,
    language: str,
) -> str:
    base = load_base_prompt()
    template = load_campaign_prompt()
    goal_line = goal or "personal branding and job opportunities"
    lang_line = "fa-en" if language == "fa-en" else "en"
    return (
        f"{base}\n\n## Campaign Task\n{template}\n\n"
        f"Niche: {niche}\n"
        f"Goal: {goal_line}\n"
        f"Language: {lang_line}"
    )


def _to_post_response(
    output: ContentPostLLMOutput,
    topic: str,
    post_type: PostType,
) -> ContentPostResponse:
    result = ContentPostResult(
        topic=topic,
        post_type=post_type,
        full_post=output.full_post,
        hooks=output.hooks,
        cta=output.cta,
        hashtags=output.hashtags,
        first_comment=output.first_comment,
    )
    return ContentPostResponse(
        result=result,
        understanding=output.understanding,
        strategic_reasoning=output.strategic_reasoning,
        execution_tips=output.execution_tips,
        alternatives=output.alternative_angles,
        follow_up_question=output.follow_up_question,
    )


def post_response_to_linkaid(response: ContentPostResponse) -> LinkAidResponse:
    hooks_block = "\n".join(
        f"• [{h.style}] {h.hook} _(save tip: {h.save_optimization_hint})_"
        for h in response.result.hooks
    )
    hashtags = " ".join(response.result.hashtags)
    main = (
        f"**۳ هوک پیشنهادی (یکی را انتخاب کن):**\n{hooks_block}\n\n"
        f"---\n\n{response.result.full_post}\n\n"
        f"**CTA:** {response.result.cta}\n\n"
        f"**Hashtags:** {hashtags}\n\n"
        f"**First comment:** {response.result.first_comment}"
    )
    return LinkAidResponse(
        understanding=response.understanding,
        main_recommendation=main,
        alternatives=response.alternatives,
        strategic_reasoning=response.strategic_reasoning,
        execution_tips=response.execution_tips,
        follow_up_question=response.follow_up_question,
    )


class ContentService:
    def __init__(self, llm_service: LLMService) -> None:
        self.llm = llm_service

    async def generate_post(self, request: ContentPostRequest) -> ContentPostResponse:
        system = build_post_system_prompt(
            request.post_type,
            request.topic,
            request.language,
            request.tone,
        )
        output = await self.llm.structured_invoke(
            [
                SystemMessage(content=system),
                HumanMessage(
                    content=f"Create a {request.post_type} LinkedIn post about: {request.topic}"
                ),
            ],
            ContentPostLLMOutput,
        )
        if not isinstance(output, ContentPostLLMOutput):
            output = ContentPostLLMOutput.model_validate(output)

        logger.info("Generated %s post for topic=%s", request.post_type, request.topic)
        return _to_post_response(output, request.topic, request.post_type)

    async def generate_campaign(
        self, request: ContentCampaignRequest
    ) -> ContentCampaignResponse:
        system = build_campaign_system_prompt(
            request.niche, request.goal, request.language
        )
        plan = await self.llm.structured_invoke(
            [
                SystemMessage(content=system),
                HumanMessage(
                    content=f"Create a 30-day content campaign for niche: {request.niche}"
                ),
            ],
            CampaignPlan,
        )
        if not isinstance(plan, CampaignPlan):
            plan = CampaignPlan.model_validate(plan)

        logger.info("Generated 30-day campaign for niche=%s", request.niche)
        return ContentCampaignResponse(
            plan=plan,
            strategic_reasoning=(
                "Document/carousel days are placed on high-engagement slots. "
                "Saves-focused content dominates 2026 distribution."
            ),
            execution_tips=(
                "Publish 2–5 posts per week from this plan. "
                "Batch-create carousels on weekends. Engage in first 60 minutes."
            ),
            follow_up_question="Which week should we expand into full post drafts first?",
        )

    async def generate_from_messages(
        self,
        messages: list[BaseMessage],
        user_context: dict | None = None,
        post_type: PostType = "text",
    ) -> ContentPostResponse:
        last = messages[-1]
        topic = last.content if isinstance(last.content, str) else str(last.content)
        request = ContentPostRequest(topic=topic, post_type=post_type)
        system = build_post_system_prompt(
            post_type, topic, request.language, request.tone, user_context
        )
        output = await self.llm.structured_invoke(
            [SystemMessage(content=system), *messages],
            ContentPostLLMOutput,
        )
        if not isinstance(output, ContentPostLLMOutput):
            output = ContentPostLLMOutput.model_validate(output)
        return _to_post_response(output, topic, post_type)
