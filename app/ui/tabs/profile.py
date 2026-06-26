"""Profile Optimization tab."""

from __future__ import annotations

import streamlit as st

from app.ui.api_client import LinkAidAPIError, LinkAidClient
from app.ui.components import render_api_error, render_text_block


def render_profile_tab(client: LinkAidClient, language_mix: str) -> None:
    st.subheader("Profile Optimization")

    with st.form("profile_form"):
        section = st.selectbox(
            "Section",
            ["headline", "about", "experience", "featured", "skills", "full"],
        )
        current_content = st.text_area(
            "Current content",
            height=120,
            placeholder="Paste your current headline, about, etc.",
        )
        role = st.text_input("Role (optional)", placeholder="Senior Backend Engineer")
        years = st.number_input("Years of experience", min_value=0, max_value=40, value=5)
        submitted = st.form_submit_button("Optimize", type="primary")

    if not submitted:
        return
    if not current_content.strip():
        st.warning("Please paste your current content.")
        return

    payload = {
        "section": section,
        "current_content": current_content.strip(),
        "role": role or None,
        "years_experience": years or None,
    }

    with st.spinner("Optimizing…"):
        try:
            data = client.optimize_profile(payload)
            _render_profile_result(data, section, language_mix)
        except LinkAidAPIError as exc:
            render_api_error(exc)


def _render_profile_result(data: dict, section: str, language_mix: str) -> None:
    result = data.get("result", {})

    if section == "headline":
        for i, variant in enumerate(result.get("headlines", result.get("variants", []))):
            text = variant.get("headline", variant.get("content", str(variant)))
            reasoning = variant.get("reasoning", "")
            body = f"{text}\n_{reasoning}_" if reasoning else text
            render_text_block(
                f"Headline {i + 1} ({len(text)} chars)",
                body,
                key=f"prof-headline-{i}",
                language_mix=language_mix,
            )
    elif section == "about":
        render_text_block(
            "Optimized About",
            result.get("about", result.get("optimized_content", "")),
            key="prof-about",
            language_mix=language_mix,
        )
    else:
        optimized = result.get("optimized_content") or result.get("full_profile") or str(result)
        render_text_block("Optimized", optimized, key="prof-main", language_mix=language_mix)

    render_text_block(
        "Strategic Reasoning",
        data.get("strategic_reasoning", ""),
        key="prof-strategy",
        language_mix=language_mix,
    )
    render_text_block(
        "Execution Tips",
        data.get("execution_tips", ""),
        key="prof-tips",
        language_mix=language_mix,
    )
