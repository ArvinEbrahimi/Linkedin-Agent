"""Networking Engine tab."""

from __future__ import annotations

import streamlit as st

from app.ui.api_client import LinkAidAPIError, LinkAidClient
from app.ui.components import render_api_error, render_text_block


def render_networking_tab(client: LinkAidClient, user_id: str, language_mix: str) -> None:
    st.subheader("Networking Engine")
    mode = st.radio("Mode", ["Profile SWOT", "Outreach sequence"], horizontal=True)

    with st.form("networking_form"):
        profile_text = st.text_area(
            "Target profile text (paste from LinkedIn)",
            height=150,
            placeholder="Name, headline, about, recent activity…",
        )
        your_context = st.text_input(
            "Your context (optional)",
            placeholder="Senior backend engineer seeking remote roles",
        )
        require_review = False
        if mode == "Outreach sequence":
            require_review = st.checkbox(
                "Flag for manual review before sending",
                value=True,
            )
        submitted = st.form_submit_button("Analyze", type="primary")

    if not submitted:
        return
    if not profile_text or len(profile_text.strip()) < 20:
        st.warning("Profile text must be at least 20 characters.")
        return

    with st.spinner("Analyzing…"):
        try:
            if mode == "Profile SWOT":
                data = client.analyze_profile(
                    {
                        "profile_text": profile_text.strip(),
                        "user_id": user_id,
                        "your_context": your_context or None,
                    }
                )
                _render_analysis(data, language_mix)
            else:
                data = client.generate_outreach(
                    {
                        "profile_text": profile_text.strip(),
                        "user_id": user_id,
                        "your_context": your_context or None,
                        "require_hitl_review": require_review,
                    }
                )
                _render_outreach(data, language_mix)
        except LinkAidAPIError as exc:
            render_api_error(exc)


def _render_analysis(data: dict, language_mix: str) -> None:
    result = data.get("result", {})
    render_text_block(
        "Summary",
        result.get("summary", ""),
        key="net-summary",
        language_mix=language_mix,
    )

    swot = result.get("swot", {})
    swot_text = (
        f"**Strengths:** {', '.join(swot.get('strengths', []))}\n"
        f"**Weaknesses:** {', '.join(swot.get('weaknesses', []))}\n"
        f"**Opportunities:** {', '.join(swot.get('opportunities', []))}\n"
        f"**Threats:** {', '.join(swot.get('threats', []))}"
    )
    render_text_block("SWOT", swot_text, key="net-swot", language_mix=language_mix)

    icebreakers = "\n".join(f"• {ib}" for ib in result.get("icebreakers", []))
    render_text_block("Icebreakers", icebreakers, key="net-ice", language_mix=language_mix)

    conn = result.get("connection_request", "")
    render_text_block(
        f"Connection Request ({len(conn)} chars)",
        conn,
        key="net-conn",
        language_mix=language_mix,
    )
    render_text_block(
        "Execution Tips",
        data.get("execution_tips", ""),
        key="net-tips",
        language_mix=language_mix,
    )


def _render_outreach(data: dict, language_mix: str) -> None:
    seq = data.get("sequence", {})
    conn = seq.get("connection_request", "")
    render_text_block(
        f"Connection Request ({len(conn)} chars)",
        conn,
        key="outreach-conn",
        language_mix=language_mix,
    )
    for step in seq.get("follow_ups", []):
        body = step.get("body", "")
        if step.get("subject"):
            body = f"Subject: {step['subject']}\n{body}"
        render_text_block(
            f"Step {step.get('step')} — {step.get('channel')} ({step.get('timing')})",
            body,
            key=f"outreach-step-{step.get('step')}",
            language_mix=language_mix,
        )
    if data.get("hitl_required"):
        st.warning("⚠️ Review this outreach manually before sending.")
