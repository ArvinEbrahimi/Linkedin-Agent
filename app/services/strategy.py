import logging
from pathlib import Path

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.models.responses import LinkAidResponse
from app.models.strategy import (
    CalendarLLMOutput,
    CalendarRequest,
    CalendarResponse,
    CompetitorLLMOutput,
    CompetitorRequest,
    CompetitorResponse,
    NarrativeLLMOutput,
    NarrativeRequest,
    NarrativeResponse,
    StrategyMode,
)
from app.services.llm import LLMService, load_base_prompt
from app.services.memory_store import MemoryService
from app.services.search import SearchService

logger = logging.getLogger(__name__)

STRATEGY_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "agents" / "prompts" / "strategy"


def load_strategy_prompt(name: str) -> str:
    return (STRATEGY_PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def _build_strategy_system(mode: str, user_context: dict, extra: str = "") -> str:
    base = load_base_prompt()
    template = load_strategy_prompt(mode)
    ctx = f"\n\n## Stored User Context\n{user_context}" if user_context else ""
    extra_block = f"\n\n## Additional Context\n{extra}" if extra else ""
    return f"{base}\n\n## Strategy Task\n{template}{ctx}{extra_block}"


def detect_strategy_mode(text: str) -> StrategyMode:
    lower = text.lower()
    competitor_kw = ("competitor", "rival", "vs ", "versus", "مقایسه", "رقیب", "competition")
    calendar_kw = ("calendar", "schedule", "تقویم", "برنامه محتوا", "content plan", "weekly plan")
    if any(k in lower for k in competitor_kw):
        return "competitor"
    if any(k in lower for k in calendar_kw):
        return "calendar"
    return "narrative"


def narrative_to_linkaid(response: NarrativeResponse) -> LinkAidResponse:
    n = response.narrative
    main = (
        f"**Positioning:** {n.positioning_statement}\n\n"
        f"**Elevator Pitch:**\n{n.elevator_pitch}\n\n"
        f"**UVP:** {n.unique_value_proposition}\n\n"
        f"**Audience:** {n.target_audience_summary}\n\n"
        f"**Tone:** {', '.join(n.tone_keywords)}"
    )
    return LinkAidResponse(
        understanding=response.understanding,
        main_recommendation=main,
        alternatives=response.alternatives,
        strategic_reasoning=response.strategic_reasoning,
        execution_tips=response.execution_tips,
        follow_up_question=response.follow_up_question,
    )


def competitor_to_linkaid(response: CompetitorResponse) -> LinkAidResponse:
    table_rows = "\n".join(
        f"| {r.competitor} | {r.their_angle} | {r.your_differentiation} | {r.content_opportunity} |"
        for r in response.comparison_table
    )
    angles = "\n".join(f"• {a}" for a in response.differentiated_angles)
    swot = response.your_swot
    main = (
        f"**Comparison Table:**\n"
        f"| Competitor | Their Angle | Your Edge | Content Opportunity |\n"
        f"|---|---|---|---|\n{table_rows}\n\n"
        f"**Differentiated Angles:**\n{angles}\n\n"
        f"**Your SWOT:** S: {', '.join(swot.strengths)} | "
        f"W: {', '.join(swot.weaknesses)} | "
        f"O: {', '.join(swot.opportunities)} | "
        f"T: {', '.join(swot.threats)}"
    )
    return LinkAidResponse(
        understanding=response.understanding,
        main_recommendation=main,
        alternatives=response.alternatives,
        strategic_reasoning=response.strategic_reasoning,
        execution_tips=response.execution_tips,
        follow_up_question=response.follow_up_question,
    )


def calendar_to_linkaid(response: CalendarResponse) -> LinkAidResponse:
    by_week: dict[int, list[str]] = {}
    for slot in response.slots:
        line = (
            f"**{slot.day}** — {slot.post_type}: {slot.theme}\n"
            f"  Hook: {slot.hook_idea}\n  CTA: {slot.cta_hint}"
        )
        by_week.setdefault(slot.week, []).append(line)

    weeks_block = "\n\n".join(
        f"**Week {w}:**\n" + "\n".join(lines) for w, lines in sorted(by_week.items())
    )
    main = f"**Monthly Theme:** {response.monthly_theme}\n\n{weeks_block}"
    return LinkAidResponse(
        understanding=response.understanding,
        main_recommendation=main,
        alternatives=response.alternatives,
        strategic_reasoning=response.strategic_reasoning,
        execution_tips=response.execution_tips,
        follow_up_question=response.follow_up_question,
    )


class StrategyService:
    def __init__(
        self,
        llm_service: LLMService,
        memory_service: MemoryService,
        search_service: SearchService,
    ) -> None:
        self.llm = llm_service
        self.memory = memory_service
        self.search = search_service

    def _get_context(self, user_id: str, query: str | None = None) -> dict:
        return self.memory.get_user_context(user_id, query=query)

    async def build_narrative(self, request: NarrativeRequest) -> NarrativeResponse:
        context = self._get_context(request.user_id)
        extra_parts = []
        if request.background:
            extra_parts.append(f"Background: {request.background}")
        if request.target_audience:
            extra_parts.append(f"Target audience: {request.target_audience}")
        extra = "\n".join(extra_parts)

        system = _build_strategy_system("narrative", context, extra)
        user_msg = "Create my personal narrative and positioning for LinkedIn."
        output = await self.llm.structured_invoke(
            [SystemMessage(content=system), HumanMessage(content=user_msg)],
            NarrativeLLMOutput,
        )
        if not isinstance(output, NarrativeLLMOutput):
            output = NarrativeLLMOutput.model_validate(output)

        return NarrativeResponse(
            narrative=output.narrative,
            understanding=output.understanding,
            strategic_reasoning=output.strategic_reasoning,
            execution_tips=output.execution_tips,
            alternatives=output.alternative_angles,
            follow_up_question=output.follow_up_question,
            user_context_used=context,
        )

    async def analyze_competitors(self, request: CompetitorRequest) -> CompetitorResponse:
        context = self._get_context(request.user_id)
        niche = request.your_niche or context.get("niche")
        search_results, provider = await self.search.search_competitors(
            request.competitor_names, niche
        )
        search_block = SearchService.format_results_for_prompt(search_results)
        extra = (
            f"Competitors to analyze: {', '.join(request.competitor_names)}\n\n"
            f"## Web Search Results (provider: {provider})\n{search_block}"
        )
        system = _build_strategy_system("competitor", context, extra)
        user_msg = (
            f"Analyze these competitors and show how I can differentiate: "
            f"{', '.join(request.competitor_names)}"
        )
        output = await self.llm.structured_invoke(
            [SystemMessage(content=system), HumanMessage(content=user_msg)],
            CompetitorLLMOutput,
        )
        if not isinstance(output, CompetitorLLMOutput):
            output = CompetitorLLMOutput.model_validate(output)

        sources = [r.url for r in search_results if r.url]
        return CompetitorResponse(
            competitors=output.competitors,
            comparison_table=output.comparison_table,
            differentiated_angles=output.differentiated_angles,
            your_swot=output.your_swot,
            understanding=output.understanding,
            strategic_reasoning=output.strategic_reasoning,
            execution_tips=output.execution_tips,
            alternatives=output.alternative_angles,
            follow_up_question=output.follow_up_question,
            search_sources_used=sources,
            user_context_used=context,
        )

    async def build_calendar(self, request: CalendarRequest) -> CalendarResponse:
        context = self._get_context(request.user_id)
        freq = request.posting_frequency or context.get("posting_frequency", "3/week")
        themes = request.focus_themes or []
        extra = (
            f"Calendar length: {request.weeks} weeks\n"
            f"Posting frequency: {freq}\n"
            f"Focus themes: {', '.join(themes) if themes else 'use profile niche'}"
        )
        system = _build_strategy_system("calendar", context, extra)
        user_msg = f"Build a {request.weeks}-week LinkedIn content calendar for me."
        output = await self.llm.structured_invoke(
            [SystemMessage(content=system), HumanMessage(content=user_msg)],
            CalendarLLMOutput,
        )
        if not isinstance(output, CalendarLLMOutput):
            output = CalendarLLMOutput.model_validate(output)

        return CalendarResponse(
            weeks=request.weeks,
            monthly_theme=output.monthly_theme,
            slots=output.slots,
            understanding=output.understanding,
            strategic_reasoning=output.strategic_reasoning,
            execution_tips=output.execution_tips,
            alternatives=output.alternative_angles,
            follow_up_question=output.follow_up_question,
            user_context_used=context,
        )

    async def strategize_from_messages(
        self,
        messages: list[BaseMessage],
        user_id: str,
        mode: StrategyMode | str = "narrative",
    ) -> NarrativeResponse | CompetitorResponse | CalendarResponse:
        last = messages[-1]
        content = last.content if isinstance(last.content, str) else str(last.content)

        if mode == "auto":
            mode = detect_strategy_mode(content)

        if mode == "competitor":
            context = self._get_context(user_id, query=content[:200])
            names = _extract_competitor_names(content, context.get("competitors", []))
            return await self.analyze_competitors(
                CompetitorRequest(user_id=user_id, competitor_names=names)
            )
        if mode == "calendar":
            weeks = _extract_weeks(content)
            return await self.build_calendar(CalendarRequest(user_id=user_id, weeks=weeks))
        return await self.build_narrative(NarrativeRequest(user_id=user_id, background=content))


def _extract_competitor_names(text: str, stored: list[str] | None = None) -> list[str]:
    """Best-effort extraction; falls back to stored profile competitors."""
    import re

    quoted = re.findall(r'"([^"]+)"|\'([^\']+)\'', text)
    names = [q[0] or q[1] for q in quoted if q[0] or q[1]]
    if names:
        return names[:5]

    after_vs = re.search(r"(?:vs\.?|versus|against|competitors?)\s+(.+)", text, re.I)
    if after_vs:
        chunk = after_vs.group(1).strip().rstrip(".")
        parts = [p.strip() for p in re.split(r"[,،&]", chunk) if p.strip()]
        if parts:
            return parts[:5]

    if stored:
        return stored[:5]

    return ["industry peer"]


def _extract_weeks(text: str) -> int:
    import re

    match = re.search(r"(\d+)\s*-?\s*week", text, re.I)
    if match:
        return min(8, max(1, int(match.group(1))))
    return 4
