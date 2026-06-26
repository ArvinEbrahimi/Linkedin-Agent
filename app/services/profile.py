import logging
from pathlib import Path

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.models.profile import (
    ProfileOptimizeLLMOutput,
    ProfileOptimizeRequest,
    ProfileOptimizeResponse,
    ProfileSection,
    ProfileSectionResult,
)
from app.models.responses import LinkAidResponse
from app.services.llm import LLMService, load_base_prompt

logger = logging.getLogger(__name__)

PROFILE_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "agents" / "prompts" / "profile"

SECTION_PROMPT_MAP: dict[ProfileSection, str] = {
    "headline": "headline",
    "about": "about",
    "experience": "experience",
    "featured": "featured",
    "skills": "featured",
    "full": "full",
}


def load_profile_prompt(name: str) -> str:
    return (PROFILE_PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def build_profile_system_prompt(request: ProfileOptimizeRequest) -> str:
    base = load_base_prompt()
    prompt_file = SECTION_PROMPT_MAP[request.section]
    template = load_profile_prompt(prompt_file)

    section_note = ""
    if request.section == "skills":
        section_note = "\n\nFocus ONLY on top_skills and skills_to_add. Leave other sections null."

    lang = (
        "Natural Persian + technical English"
        if request.language == "fa-en"
        else "English"
    )
    context = (
        f"Role: {request.role or 'not specified'}\n"
        f"Years experience: {request.years_experience or 'not specified'}\n"
        f"Tech stack: {', '.join(request.tech_stack) or 'not specified'}\n"
        f"Target goal: {request.target_goal or 'personal branding'}\n"
        f"Language: {lang}\n"
    )
    if request.section == "experience":
        context += f"Company: {request.company or 'not specified'}\n"
        context += f"Role title: {request.role_title or 'not specified'}\n"

    return (
        f"{base}\n\n## Profile Optimization Task\n{template}{section_note}\n\n"
        f"## User Context\n{context}"
    )


def _build_section_result(
    section: ProfileSection, output: ProfileOptimizeLLMOutput
) -> ProfileSectionResult:
    return ProfileSectionResult(
        section=section,
        headlines=output.headlines,
        about=output.about,
        about_structure=output.about_structure,
        experience_bullets=output.experience_bullets,
        featured_items=output.featured_items,
        top_skills=output.top_skills,
        skills_to_add=output.skills_to_add,
    )


def _validate_section_output(
    section: ProfileSection, output: ProfileOptimizeLLMOutput
) -> None:
    if section == "headline":
        if not output.headlines or len(output.headlines) < 3:
            raise ValueError("Headline optimization requires 3 variants")
    elif section == "about":
        if not output.about:
            raise ValueError("About optimization requires about text")
    elif section == "experience":
        if not output.experience_bullets:
            raise ValueError("Experience optimization requires bullets")
    elif section == "featured":
        if not output.featured_items:
            raise ValueError("Featured optimization requires items")
    elif section == "skills":
        if not output.top_skills:
            raise ValueError("Skills optimization requires top_skills")


def profile_to_linkaid(response: ProfileOptimizeResponse) -> LinkAidResponse:
    result = response.result
    section = result.section

    if section == "headline" and result.headlines:
        variants = "\n\n".join(
            f"**{i + 1}.** {h.headline}\n"
            f"   Keywords: {', '.join(h.keywords)}\n"
            f"   _{h.reasoning}_"
            for i, h in enumerate(result.headlines)
        )
        main = f"**۳ Headline پیشنهادی:**\n\n{variants}"
    elif section == "about" and result.about:
        main = f"**About (Problem → Proof → CTA):**\n\n{result.about}"
        if result.about_structure:
            main += f"\n\n**Structure:** {result.about_structure}"
    elif section == "experience" and result.experience_bullets:
        bullets = "\n".join(
            f"• {b.rewritten}" + (f" _(was: {b.original})_" if b.original else "")
            for b in result.experience_bullets
        )
        main = f"**Experience Bullets:**\n\n{bullets}"
    elif section == "featured" and result.featured_items:
        items = "\n".join(
            f"• **{item.title}** ({item.content_type}): {item.description}"
            for item in result.featured_items
        )
        skills = ""
        if result.top_skills:
            skills = f"\n\n**Top Skills:** {', '.join(result.top_skills)}"
        main = f"**Featured Items:**\n{items}{skills}"
    elif section == "skills":
        main = (
            f"**Top Skills:** {', '.join(result.top_skills or [])}\n\n"
            f"**Add These Skills:** {', '.join(result.skills_to_add or [])}"
        )
    else:
        parts = []
        if result.headlines:
            parts.append("Headlines: " + " | ".join(h.headline for h in result.headlines[:3]))
        if result.about:
            parts.append(f"About: {result.about[:200]}...")
        main = "\n\n".join(parts) if parts else "See section details in metadata."

    return LinkAidResponse(
        understanding=response.understanding,
        main_recommendation=main,
        alternatives=response.alternatives,
        strategic_reasoning=response.strategic_reasoning,
        execution_tips=response.execution_tips,
        follow_up_question=response.follow_up_question,
    )


PROFILE_ADVISORY_SYSTEM = """You are a LinkedIn profile strategist for software engineers.

The user is asking for guidance on improving their profile — NOT pasting text to rewrite.
Give a clear, ordered roadmap (3-5 steps) tailored to their context.
Mention headline, about, experience, featured, and skills when relevant.
Respond in the user's language (Persian if they wrote in Persian).

Structure your answer as LinkAidResponse:
- understanding: what they want
- main_recommendation: numbered step-by-step roadmap (actionable)
- alternatives: 2 optional approaches if useful
- strategic_reasoning: why this order works in 2026 LinkedIn algorithm
- execution_tips: quick wins for this week
- follow_up_question: one specific next question"""


def _is_profile_advisory(text: str) -> bool:
    normalized = text.strip().lower()
    if len(normalized) > 280:
        return False
    advisory_markers = (
        "از کجا شروع",
        "چطور بهتر",
        "چگونه بهتر",
        "بهتر کنم",
        "بهبود",
        "راهنمایی",
        "کمک کن",
        "where to start",
        "how to improve",
        "how do i improve",
        "what should i",
        "which section",
        "کدوم بخش",
        "اول چی",
        "first step",
    )
    if any(marker in normalized for marker in advisory_markers):
        return True
    return "?" in normalized and len(normalized) < 160


def _infer_profile_section(text: str) -> ProfileSection:
    normalized = text.lower()
    if any(w in normalized for w in ("headline", "عنوان", "تیتر", "head line")):
        return "headline"
    if any(w in normalized for w in ("about", "درباره", "bio", "بیو")):
        return "about"
    if any(w in normalized for w in ("experience", "سوابق", "تجربه")):
        return "experience"
    if any(w in normalized for w in ("skill", "مهارت")):
        return "skills"
    if any(w in normalized for w in ("featured", "برجسته")):
        return "featured"
    return "full"


def _profile_baseline_from_context(ctx: dict) -> str:
    parts = []
    if ctx.get("linkedin_headline"):
        parts.append(f"Headline: {ctx['linkedin_headline']}")
    if ctx.get("about_summary"):
        parts.append(f"About: {ctx['about_summary']}")
    if ctx.get("niche"):
        parts.append(f"Niche: {ctx['niche']}")
    if ctx.get("role"):
        parts.append(f"Role: {ctx['role']}")
    if ctx.get("goals"):
        parts.append(f"Goals: {', '.join(ctx['goals'])}")
    if ctx.get("tech_stack"):
        parts.append(f"Tech: {', '.join(ctx['tech_stack'])}")
    return "\n".join(parts)


class ProfileService:
    def __init__(self, llm_service: LLMService) -> None:
        self.llm = llm_service

    async def optimize(self, request: ProfileOptimizeRequest) -> ProfileOptimizeResponse:
        system = build_profile_system_prompt(request)
        user_msg = (
            f"Optimize the {request.section} section.\n\n"
            f"Current content:\n{request.current_content}"
        )

        output = await self.llm.structured_invoke(
            [SystemMessage(content=system), HumanMessage(content=user_msg)],
            ProfileOptimizeLLMOutput,
        )
        if not isinstance(output, ProfileOptimizeLLMOutput):
            output = ProfileOptimizeLLMOutput.model_validate(output)

        _validate_section_output(request.section, output)

        result = _build_section_result(request.section, output)
        logger.info("Profile optimized section=%s", request.section)

        return ProfileOptimizeResponse(
            result=result,
            understanding=output.understanding,
            strategic_reasoning=output.strategic_reasoning,
            execution_tips=output.execution_tips,
            alternatives=output.alternative_angles,
            follow_up_question=output.follow_up_question,
        )

    async def advise_from_messages(
        self,
        messages: list[BaseMessage],
        user_context: dict | None = None,
    ) -> LinkAidResponse:
        ctx = user_context or {}
        baseline = _profile_baseline_from_context(ctx)
        context_block = f"\n\n## Saved profile context\n{baseline}" if baseline else (
            "\n\n## Saved profile context\n(No profile saved yet — give a generic engineer roadmap.)"
        )
        system = f"{load_base_prompt()}\n\n{PROFILE_ADVISORY_SYSTEM}{context_block}"
        return await self.llm.structured_invoke(
            [SystemMessage(content=system), *messages],
            LinkAidResponse,
        )

    async def optimize_from_messages(
        self,
        messages: list[BaseMessage],
        user_context: dict | None = None,
        section: ProfileSection = "headline",
        *,
        current_content: str | None = None,
    ) -> ProfileOptimizeResponse:
        last = messages[-1]
        content = current_content or (
            last.content if isinstance(last.content, str) else str(last.content)
        )
        ctx = user_context or {}
        return await self.optimize(
            ProfileOptimizeRequest(
                section=section,
                current_content=content,
                role=ctx.get("role"),
                years_experience=ctx.get("years_experience"),
                tech_stack=ctx.get("tech_stack", []),
                target_goal=(ctx.get("goals") or [None])[0] if ctx.get("goals") else None,
            )
        )
