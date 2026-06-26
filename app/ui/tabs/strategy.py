"""Strategy & Branding tab."""

from __future__ import annotations

import streamlit as st

from app.ui.api_client import LinkAidAPIError, LinkAidClient
from app.ui.components import render_api_error, render_linkaid_response, render_text_block


def render_strategy_tab(client: LinkAidClient, user_id: str, language_mix: str) -> None:
    st.subheader("Strategy & Branding")
    mode = st.radio(
        "Mode",
        ["Personal narrative", "Competitor analysis", "Content calendar"],
        horizontal=True,
    )

    if mode == "Personal narrative":
        with st.form("narrative_form"):
            background = st.text_area("Extra background (optional)", height=80)
            audience = st.text_input("Target audience override (optional)")
            submitted = st.form_submit_button("Build narrative", type="primary")
        if submitted:
            _run_narrative(client, user_id, background, audience, language_mix)
        return

    if mode == "Competitor analysis":
        with st.form("competitor_form"):
            competitors = st.text_input(
                "Competitor names (comma-separated)",
                placeholder="Alice Dev, Bob ML",
            )
            niche = st.text_input("Your niche (optional override)")
            submitted = st.form_submit_button("Analyze competitors", type="primary")
        if submitted:
            names = [n.strip() for n in competitors.split(",") if n.strip()]
            if not names:
                st.warning("Enter at least one competitor name.")
                return
            with st.spinner("Researching competitors…"):
                try:
                    data = client.analyze_competitors(
                        {
                            "user_id": user_id,
                            "competitor_names": names,
                            "your_niche": niche or None,
                        }
                    )
                    _render_competitor(data, language_mix)
                except LinkAidAPIError as exc:
                    render_api_error(exc)
        return

    with st.form("calendar_form"):
        weeks = st.slider("Weeks", 1, 8, 4)
        frequency = st.selectbox(
            "Posting frequency",
            ["1-2/week", "2-5/week", "5+/week"],
        )
        themes = st.text_input("Focus themes (comma-separated, optional)")
        submitted = st.form_submit_button("Build calendar", type="primary")

    if submitted:
        focus = [t.strip() for t in themes.split(",") if t.strip()] or None
        with st.spinner("Building calendar…"):
            try:
                data = client.build_calendar(
                    {
                        "user_id": user_id,
                        "weeks": weeks,
                        "posting_frequency": frequency,
                        "focus_themes": focus,
                    }
                )
                _render_calendar(data, language_mix)
            except LinkAidAPIError as exc:
                render_api_error(exc)


def _run_narrative(
    client: LinkAidClient,
    user_id: str,
    background: str,
    audience: str,
    language_mix: str,
) -> None:
    with st.spinner("Crafting narrative…"):
        try:
            data = client.build_narrative(
                {
                    "user_id": user_id,
                    "background": background or None,
                    "target_audience": audience or None,
                }
            )
            narrative = data.get("narrative", {})
            main = (
                f"**Positioning:** {narrative.get('positioning_statement', '')}\n\n"
                f"**Elevator Pitch:**\n{narrative.get('elevator_pitch', '')}\n\n"
                f"**UVP:** {narrative.get('unique_value_proposition', '')}\n\n"
                f"**Audience:** {narrative.get('target_audience_summary', '')}\n\n"
                f"**Tone:** {', '.join(narrative.get('tone_keywords', []))}"
            )
            response = {
                "understanding": data.get("understanding", ""),
                "main_recommendation": main,
                "alternatives": data.get("alternatives", []),
                "strategic_reasoning": data.get("strategic_reasoning", ""),
                "execution_tips": data.get("execution_tips", ""),
                "follow_up_question": data.get("follow_up_question", ""),
            }
            render_linkaid_response(
                response,
                prefix="strategy-narrative",
                language_mix=language_mix,
            )
        except LinkAidAPIError as exc:
            render_api_error(exc)


def _render_competitor(data: dict, language_mix: str) -> None:
    rows = data.get("comparison_table", [])
    if rows:
        st.markdown("**Comparison Table**")
        table_md = "| Competitor | Their Angle | Your Edge | Opportunity |\n|---|---|---|---|\n"
        for row in rows:
            table_md += (
                f"| {row.get('competitor')} | {row.get('their_angle')} | "
                f"{row.get('your_differentiation')} | {row.get('content_opportunity')} |\n"
            )
        st.markdown(table_md)

    angles = "\n".join(f"• {a}" for a in data.get("differentiated_angles", []))
    render_text_block(
        "Differentiated Angles",
        angles,
        key="strat-angles",
        language_mix=language_mix,
    )

    swot = data.get("your_swot", {})
    swot_text = (
        f"S: {', '.join(swot.get('strengths', []))} | "
        f"W: {', '.join(swot.get('weaknesses', []))} | "
        f"O: {', '.join(swot.get('opportunities', []))} | "
        f"T: {', '.join(swot.get('threats', []))}"
    )
    render_text_block("Your SWOT", swot_text, key="strat-swot", language_mix=language_mix)

    if data.get("search_sources_used"):
        with st.expander("Search sources used"):
            for url in data["search_sources_used"]:
                st.markdown(f"- {url}")


def _render_calendar(data: dict, language_mix: str) -> None:
    render_text_block(
        "Monthly Theme",
        data.get("monthly_theme", ""),
        key="strat-theme",
        language_mix=language_mix,
    )
    by_week: dict[int, list] = {}
    for slot in data.get("slots", []):
        by_week.setdefault(slot.get("week", 1), []).append(slot)

    for week in sorted(by_week):
        lines = []
        for slot in by_week[week]:
            lines.append(
                f"**{slot.get('day')}** — {slot.get('post_type')}: {slot.get('theme')}\n"
                f"  Hook: {slot.get('hook_idea')}\n  CTA: {slot.get('cta_hint')}"
            )
        render_text_block(
            f"Week {week}",
            "\n\n".join(lines),
            key=f"strat-week-{week}",
            language_mix=language_mix,
        )

    render_text_block(
        "Execution Tips",
        data.get("execution_tips", ""),
        key="strat-tips",
        language_mix=language_mix,
    )
