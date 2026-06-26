"""Content Intelligence tab."""

from __future__ import annotations

import streamlit as st

from app.ui.api_client import LinkAidAPIError, LinkAidClient
from app.ui.components import copy_button, render_api_error, render_text_block


def render_content_tab(client: LinkAidClient, language_mix: str) -> None:
    st.subheader("Content Intelligence")
    mode = st.radio("Mode", ["Single post", "30-day campaign"], horizontal=True)

    with st.form("content_form"):
        topic = st.text_input("Topic / موضوع", placeholder="FastAPI performance tips")
        post_type = st.selectbox(
            "Post type",
            ["text", "carousel", "video", "poll", "document"],
        )
        tone = st.text_input("Tone (optional)", placeholder="professional, warm, bold")
        language = st.selectbox(
            "Language",
            ["fa-en", "en"],
            index=0 if language_mix == "fa-en" else 1,
        )
        submitted = st.form_submit_button("Generate", type="primary")

    if not submitted:
        return
    if not topic or len(topic.strip()) < 3:
        st.warning("Topic must be at least 3 characters.")
        return

    payload = {
        "topic": topic.strip(),
        "post_type": post_type,
        "tone": tone or None,
        "language": language,
    }

    with st.spinner("Generating content…"):
        try:
            if mode == "Single post":
                data = client.generate_post(payload)
                _render_post_result(data, language_mix)
            else:
                data = client.generate_campaign(
                    {
                        "niche": topic.strip(),
                        "language": language,
                    }
                )
                _render_campaign_result(data, language_mix)
        except LinkAidAPIError as exc:
            render_api_error(exc)


def _render_post_result(data: dict, language_mix: str) -> None:
    result = data["result"]
    render_text_block(
        "Full Post",
        result["full_post"],
        key="content-post",
        language_mix=language_mix,
    )
    render_text_block("CTA", result["cta"], key="content-cta", language_mix=language_mix)
    render_text_block(
        "First Comment",
        result["first_comment"],
        key="content-comment",
        language_mix=language_mix,
    )
    if result.get("hashtags"):
        tags = " ".join(result["hashtags"])
        render_text_block("Hashtags", tags, key="content-tags", language_mix=language_mix)

    st.markdown("**Hooks**")
    for i, hook in enumerate(result.get("hooks", [])):
        hint = hook.get("save_optimization_hint", "")
        text = f"{hook['hook']}\n_Style: {hook['style']}_ — {hint}"
        render_text_block(
            f"Hook {i + 1}",
            text,
            key=f"content-hook-{i}",
            language_mix=language_mix,
        )

    render_text_block(
        "Strategic Reasoning",
        data.get("strategic_reasoning", ""),
        key="content-strategy",
        language_mix=language_mix,
    )
    render_text_block(
        "Execution Tips",
        data.get("execution_tips", ""),
        key="content-tips",
        language_mix=language_mix,
    )


def _render_campaign_result(data: dict, language_mix: str) -> None:
    plan = data.get("plan", {})
    render_text_block(
        "Campaign",
        plan.get("campaign_name", "30-day campaign"),
        key="campaign-name",
        language_mix=language_mix,
    )

    themes = plan.get("weekly_themes", [])
    if themes:
        render_text_block(
            "Weekly Themes",
            "\n".join(f"• {t}" for t in themes),
            key="campaign-weekly-themes",
            language_mix=language_mix,
        )

    days = plan.get("days", [])
    for day in days[:10]:
        body = (
            f"**{day.get('title')}** ({day.get('post_type')})\n"
            f"Theme: {day.get('theme')}\n"
            f"Hook: {day.get('hook_idea')}\n"
            f"Key message: {day.get('key_message')}"
        )
        render_text_block(
            f"Day {day.get('day')}",
            body,
            key=f"campaign-day-{day.get('day')}",
            language_mix=language_mix,
        )
    if len(days) > 10:
        st.caption(f"+ {len(days) - 10} more days in the full plan")

    render_text_block(
        "Strategic Reasoning",
        data.get("strategic_reasoning", ""),
        key="campaign-strategy",
        language_mix=language_mix,
    )
    render_text_block(
        "Execution Tips",
        data.get("execution_tips", ""),
        key="campaign-tips",
        language_mix=language_mix,
    )

    all_days = "\n\n".join(
        f"Day {d.get('day')}: {d.get('title')} — {d.get('hook_idea')}" for d in days
    )
    copy_button("Copy full campaign outline", all_days, key="campaign-copy-all")
