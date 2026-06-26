import logging
from pathlib import Path

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.models.networking import (
    OutreachLLMOutput,
    OutreachRequest,
    OutreachResponse,
    OutreachSequence,
    ProfileAnalysisLLMOutput,
    ProfileAnalysisResult,
    ProfileAnalyzeRequest,
    ProfileAnalyzeResponse,
)
from app.models.responses import LinkAidResponse
from app.services.llm import LLMService, load_base_prompt
from app.services.rate_limit import OutreachRateLimiter

logger = logging.getLogger(__name__)

NETWORKING_PROMPTS_DIR = (
    Path(__file__).resolve().parent.parent / "agents" / "prompts" / "networking"
)

HITL_REVIEW_NOTE = (
    "⚠️ این پیشنهاد نیاز به بررسی دستی دارد قبل از ارسال. "
    "LinkAid فقط پیشنهاد می‌دهد — شما تصمیم نهایی را می‌گیرید."
)


def load_networking_prompt(name: str) -> str:
    return (NETWORKING_PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def build_analyze_system_prompt(your_context: str | None) -> str:
    base = load_base_prompt()
    template = load_networking_prompt("analyze")
    ctx = f"\nYour context: {your_context}" if your_context else ""
    return f"{base}\n\n## Networking Task\n{template}{ctx}"


def build_outreach_system_prompt(your_context: str | None) -> str:
    base = load_base_prompt()
    template = load_networking_prompt("outreach")
    ctx = f"\nYour context: {your_context}" if your_context else ""
    return f"{base}\n\n## Outreach Task\n{template}{ctx}"


def analysis_to_linkaid(response: ProfileAnalyzeResponse) -> LinkAidResponse:
    swot = response.result.swot
    swot_block = (
        f"**Strengths:** {', '.join(swot.strengths)}\n"
        f"**Weaknesses:** {', '.join(swot.weaknesses)}\n"
        f"**Opportunities:** {', '.join(swot.opportunities)}\n"
        f"**Threats:** {', '.join(swot.threats)}"
    )
    icebreakers = "\n".join(f"• {ib}" for ib in response.result.icebreakers)
    main = (
        f"**Summary:** {response.result.summary}\n\n"
        f"**SWOT:**\n{swot_block}\n\n"
        f"**Icebreakers:**\n{icebreakers}\n\n"
        f"**Connection Request ({len(response.result.connection_request)} chars):**\n"
        f"{response.result.connection_request}"
    )
    return LinkAidResponse(
        understanding=response.understanding,
        main_recommendation=main,
        alternatives=response.alternatives,
        strategic_reasoning=response.strategic_reasoning,
        execution_tips=response.execution_tips,
        follow_up_question=response.follow_up_question,
    )


def outreach_to_linkaid(response: OutreachResponse) -> LinkAidResponse:
    seq = response.sequence
    followups = "\n\n".join(
        f"**Step {s.step} ({s.channel}, {s.timing}):**\n"
        + (f"Subject: {s.subject}\n" if s.subject else "")
        + s.body
        for s in seq.follow_ups
    )
    review = f"\n\n{response.review_note}" if response.review_note else ""
    main = (
        f"**Connection Request ({len(seq.connection_request)} chars):**\n"
        f"{seq.connection_request}\n\n"
        f"**Follow-up Sequence:**\n{followups}{review}"
    )
    return LinkAidResponse(
        understanding=response.understanding,
        main_recommendation=main,
        alternatives=response.alternatives,
        strategic_reasoning=response.strategic_reasoning,
        execution_tips=response.execution_tips,
        follow_up_question=response.follow_up_question,
    )


class NetworkingService:
    def __init__(
        self,
        llm_service: LLMService,
        rate_limiter: OutreachRateLimiter,
    ) -> None:
        self.llm = llm_service
        self.rate_limiter = rate_limiter

    async def analyze_profile(self, request: ProfileAnalyzeRequest) -> ProfileAnalyzeResponse:
        system = build_analyze_system_prompt(request.your_context)
        output = await self.llm.structured_invoke(
            [
                SystemMessage(content=system),
                HumanMessage(content=f"Analyze this LinkedIn profile:\n\n{request.profile_text}"),
            ],
            ProfileAnalysisLLMOutput,
        )
        if not isinstance(output, ProfileAnalysisLLMOutput):
            output = ProfileAnalysisLLMOutput.model_validate(output)

        result = ProfileAnalysisResult(
            summary=output.summary,
            swot=output.swot,
            icebreakers=output.icebreakers,
            connection_request=output.connection_request,
        )
        logger.info("Profile analyzed chars=%d", len(request.profile_text))
        return ProfileAnalyzeResponse(
            result=result,
            understanding=output.understanding,
            strategic_reasoning=output.strategic_reasoning,
            execution_tips=output.execution_tips,
            alternatives=output.alternative_angles,
            follow_up_question=output.follow_up_question,
        )

    async def generate_outreach(self, request: OutreachRequest) -> OutreachResponse:
        remaining = self.rate_limiter.check_and_increment(request.user_id)

        system = build_outreach_system_prompt(request.your_context)
        output = await self.llm.structured_invoke(
            [
                SystemMessage(content=system),
                HumanMessage(
                    content=f"Create outreach sequence for this profile:\n\n{request.profile_text}"
                ),
            ],
            OutreachLLMOutput,
        )
        if not isinstance(output, OutreachLLMOutput):
            output = OutreachLLMOutput.model_validate(output)

        requires_review = request.require_hitl_review or len(output.sensitive_flags) > 0
        review_note = None
        if requires_review:
            flags = (
                ", ".join(output.sensitive_flags) if output.sensitive_flags else "user requested"
            )
            review_note = f"{HITL_REVIEW_NOTE} Flags: {flags}"

        sequence = OutreachSequence(
            connection_request=output.connection_request,
            follow_ups=output.follow_ups,
        )
        logger.info(
            "Outreach generated user=%s requires_review=%s remaining=%d",
            request.user_id,
            requires_review,
            remaining,
        )
        return OutreachResponse(
            sequence=sequence,
            understanding=output.understanding,
            strategic_reasoning=output.strategic_reasoning,
            execution_tips=output.execution_tips,
            alternatives=output.alternative_angles,
            follow_up_question=output.follow_up_question,
            requires_review=requires_review,
            review_note=review_note,
            daily_remaining=remaining,
        )

    async def analyze_from_messages(
        self,
        messages: list[BaseMessage],
        user_context: dict | None = None,
    ) -> ProfileAnalyzeResponse:
        last = messages[-1]
        profile_text = last.content if isinstance(last.content, str) else str(last.content)
        your_context = user_context.get("your_context") if user_context else None
        return await self.analyze_profile(
            ProfileAnalyzeRequest(profile_text=profile_text, your_context=your_context)
        )
