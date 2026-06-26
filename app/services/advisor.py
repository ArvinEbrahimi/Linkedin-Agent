import logging
from pathlib import Path

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

from app.models.advisor import (
    AdvisorLLMOutput,
    AdvisorResponse,
    BriefingRequest,
    OutreachListRequest,
    PostAnalysisRequest,
)
from app.models.responses import LinkAidResponse
from app.services.llm import LLMService, load_base_prompt
from app.services.memory_store import MemoryService

logger = logging.getLogger(__name__)

ADVISOR_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "agents" / "prompts" / "advisor"


class ThreadSummaryOutput(BaseModel):
    summary: str


def load_advisor_prompt(name: str) -> str:
    return (ADVISOR_PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def _build_advisor_system(mode: str, user_context: dict) -> str:
    base = load_base_prompt()
    template = load_advisor_prompt(mode)
    ctx = f"\n\n## Stored User Context\n{user_context}" if user_context else ""
    return f"{base}\n\n## Advisor Task\n{template}{ctx}"


def advisor_to_linkaid(response: AdvisorResponse) -> LinkAidResponse:
    outreach_block = ""
    if response.outreach_suggestions:
        items = "\n".join(
            f"• [{s.priority_score:.1f}] {s.target_description}: {s.suggested_action}"
            for s in response.outreach_suggestions[:5]
        )
        outreach_block = f"\n\n**Outreach Ideas:**\n{items}"

    main = f"{response.main_content}{outreach_block}"
    return LinkAidResponse(
        understanding=response.understanding,
        main_recommendation=main,
        alternatives=response.alternatives,
        strategic_reasoning=response.strategic_reasoning,
        execution_tips=response.execution_tips,
        follow_up_question=response.follow_up_question,
    )


class AdvisorService:
    def __init__(self, llm_service: LLMService, memory_service: MemoryService) -> None:
        self.llm = llm_service
        self.memory = memory_service

    def _get_context(self, user_id: str, query: str | None = None) -> dict:
        return self.memory.get_user_context(user_id, query=query)

    async def _run_advisor(
        self,
        mode: str,
        user_message: str,
        user_id: str,
        query: str | None = None,
    ) -> AdvisorResponse:
        context = self._get_context(user_id, query=query)
        system = _build_advisor_system(mode, context)
        output = await self.llm.structured_invoke(
            [SystemMessage(content=system), HumanMessage(content=user_message)],
            AdvisorLLMOutput,
        )
        if not isinstance(output, AdvisorLLMOutput):
            output = AdvisorLLMOutput.model_validate(output)

        return AdvisorResponse(
            mode=mode,
            understanding=output.understanding,
            main_content=output.main_content,
            outreach_suggestions=output.outreach_suggestions,
            strategic_reasoning=output.strategic_reasoning,
            execution_tips=output.execution_tips,
            alternatives=output.alternative_angles,
            follow_up_question=output.follow_up_question,
            user_context_used=context,
        )

    async def morning_briefing(self, request: BriefingRequest) -> AdvisorResponse:
        return await self._run_advisor(
            "briefing",
            "Generate my morning LinkedIn briefing for today.",
            request.user_id,
        )

    async def analyze_post(self, request: PostAnalysisRequest) -> AdvisorResponse:
        metrics = (
            f"Impressions: {request.impressions or 'N/A'}, "
            f"Likes: {request.likes or 'N/A'}, "
            f"Comments: {request.comments or 'N/A'}, "
            f"Saves: {request.saves or 'N/A'}"
        )
        msg = (
            f"Analyze this post performance.\n\nPost:\n{request.post_content}\n\n"
            f"Metrics: {metrics}"
        )
        return await self._run_advisor(
            "post_analysis",
            msg,
            request.user_id,
            query=request.post_content[:200],
        )

    async def outreach_suggestions(self, request: OutreachListRequest) -> AdvisorResponse:
        msg = f"Generate {request.max_suggestions} prioritized outreach suggestions for today."
        response = await self._run_advisor("outreach_list", msg, request.user_id)
        response.outreach_suggestions = response.outreach_suggestions[: request.max_suggestions]
        return response

    async def advise_from_messages(
        self,
        messages: list[BaseMessage],
        user_id: str,
        mode: str = "briefing",
    ) -> AdvisorResponse:
        last = messages[-1]
        content = last.content if isinstance(last.content, str) else str(last.content)
        return await self._run_advisor(mode, content, user_id, query=content[:200])

    async def update_thread_summary(
        self,
        user_id: str,
        thread_id: str,
        messages: list[BaseMessage],
    ) -> None:
        if len(messages) < 4:
            return

        transcript = "\n".join(
            f"{m.type}: {m.content}" for m in messages[-10:] if hasattr(m, "content")
        )
        system = "Summarize this conversation in 2-3 sentences. Keep niche, goals, and decisions."
        output = await self.llm.structured_invoke(
            [
                SystemMessage(content=system),
                HumanMessage(content=transcript),
            ],
            ThreadSummaryOutput,
        )
        if isinstance(output, ThreadSummaryOutput):
            self.memory.save_thread_summary(user_id, thread_id, output.summary)
            logger.info("Updated thread summary user=%s thread=%s", user_id, thread_id)
