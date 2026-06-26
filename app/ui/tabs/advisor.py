"""Daily Advisor tab."""

from __future__ import annotations

import streamlit as st

from app.ui.api_client import LinkAidAPIError, LinkAidClient
from app.ui.components import render_api_error, render_linkaid_response, render_text_block


def render_advisor_tab(client: LinkAidClient, user_id: str, language_mix: str) -> None:
    st.subheader("Daily Advisor")
    mode = st.radio(
        "Mode",
        ["Morning briefing", "Post analysis", "Outreach list"],
        horizontal=True,
    )

    if mode == "Morning briefing":
        if st.button("Get today's briefing", type="primary"):
            with st.spinner("Preparing briefing…"):
                try:
                    data = client.morning_briefing(user_id)
                    _render_advisor_response(data, "briefing", language_mix)
                except LinkAidAPIError as exc:
                    render_api_error(exc)
        return

    if mode == "Post analysis":
        with st.form("advisor_post_form"):
            post_content = st.text_area("Post content", height=100)
            c1, c2, c3, c4 = st.columns(4)
            impressions = c1.number_input("Impressions", min_value=0, value=0)
            likes = c2.number_input("Likes", min_value=0, value=0)
            comments = c3.number_input("Comments", min_value=0, value=0)
            saves = c4.number_input("Saves", min_value=0, value=0)
            submitted = st.form_submit_button("Analyze", type="primary")

        if submitted:
            if len(post_content.strip()) < 10:
                st.warning("Post content must be at least 10 characters.")
                return
            with st.spinner("Analyzing…"):
                try:
                    data = client.analyze_post(
                        {
                            "user_id": user_id,
                            "post_content": post_content.strip(),
                            "impressions": impressions or None,
                            "likes": likes or None,
                            "comments": comments or None,
                            "saves": saves or None,
                        }
                    )
                    _render_advisor_response(data, "post", language_mix)
                except LinkAidAPIError as exc:
                    render_api_error(exc)
        return

    max_suggestions = st.slider("Max suggestions", 5, 20, 10)
    if st.button("Get outreach suggestions", type="primary"):
        with st.spinner("Building outreach list…"):
            try:
                data = client.outreach_suggestions(user_id, max_suggestions)
                _render_advisor_response(data, "outreach", language_mix)
            except LinkAidAPIError as exc:
                render_api_error(exc)


def _render_advisor_response(data: dict, prefix: str, language_mix: str) -> None:
    response = {
        "understanding": data.get("understanding", ""),
        "main_recommendation": data.get("main_content", ""),
        "alternatives": data.get("alternatives", []),
        "strategic_reasoning": data.get("strategic_reasoning", ""),
        "execution_tips": data.get("execution_tips", ""),
        "follow_up_question": data.get("follow_up_question", ""),
    }
    render_linkaid_response(response, prefix=f"advisor-{prefix}", language_mix=language_mix)

    outreach = data.get("outreach_suggestions", [])
    if outreach:
        st.markdown("**Outreach Suggestions**")
        for i, item in enumerate(outreach):
            score = item.get("priority_score", 0)
            body = (
                f"**{item.get('target_description')}** (priority {score:.1f})\n"
                f"Reason: {item.get('reason')}\n"
                f"Action: {item.get('suggested_action')}"
            )
            render_text_block(
                f"Suggestion {i + 1}",
                body,
                key=f"advisor-out-{i}",
                language_mix=language_mix,
            )
