"""Reusable Streamlit UI components."""

from __future__ import annotations

import html
import json
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from app.ui.text_utils import should_use_rtl

DISCLAIMER_FA = (
    "⚠️ **LinkAid فقط پیشنهاد می‌دهد** — هیچ پست، پیام یا اقدامی به‌صورت خودکار "
    "در لینکدین انجام نمی‌شود. شما تصمیم نهایی را می‌گیرید."
)
DISCLAIMER_EN = (
    "⚠️ **Suggest-only** — LinkAid never posts, sends messages, or takes "
    "automated actions on LinkedIn. You decide what to use."
)


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        .linkaid-disclaimer {
            background: #fff8e6;
            border: 1px solid #f0c040;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            margin-bottom: 1rem;
            font-size: 0.95rem;
        }
        .linkaid-rtl {
            direction: rtl;
            text-align: right;
            unicode-bidi: plaintext;
        }
        .linkaid-response-block {
            background: #f8fafc;
            border-left: 4px solid #0a66c2;
            padding: 0.75rem 1rem;
            border-radius: 0 8px 8px 0;
            margin: 0.5rem 0;
            white-space: pre-wrap;
        }
        .linkaid-copy-row {
            display: flex;
            justify-content: flex-end;
            margin-top: -0.25rem;
            margin-bottom: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_disclaimer(language_mix: str = "fa-en") -> None:
    text = DISCLAIMER_FA if language_mix == "fa-en" else DISCLAIMER_EN
    rtl = should_use_rtl(text, language_mix)
    cls = "linkaid-disclaimer linkaid-rtl" if rtl else "linkaid-disclaimer"
    st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)


def copy_button(label: str, text: str, key: str) -> None:
    """One-click copy via browser clipboard API."""
    safe = json.dumps(text)
    safe_label = html.escape(label)
    components.html(
        f"""
        <div class="linkaid-copy-row">
          <button id="btn-{key}" style="
            background:#0a66c2;color:white;border:none;padding:0.35rem 0.85rem;
            border-radius:6px;cursor:pointer;font-size:0.85rem;">
            📋 {safe_label}
          </button>
        </div>
        <script>
        document.getElementById("btn-{key}").onclick = function() {{
          navigator.clipboard.writeText({safe});
          this.innerText = "✓ Copied";
          setTimeout(() => {{ this.innerHTML = "📋 {safe_label}"; }}, 2000);
        }};
        </script>
        """,
        height=42,
    )


def render_text_block(title: str, text: str, *, key: str, language_mix: str = "fa-en") -> None:
    rtl = should_use_rtl(text, language_mix)
    cls = "linkaid-response-block linkaid-rtl" if rtl else "linkaid-response-block"
    st.markdown(f"**{title}**")
    st.markdown(
        f'<div class="{cls}">{html.escape(text)}</div>',
        unsafe_allow_html=True,
    )
    copy_button("Copy", text, key=key)


def render_linkaid_response(
    response: dict[str, Any], *, prefix: str, language_mix: str = "fa-en"
) -> None:
    render_text_block(
        "Understanding",
        response.get("understanding", ""),
        key=f"{prefix}-understanding",
        language_mix=language_mix,
    )
    render_text_block(
        "Main Recommendation",
        response.get("main_recommendation", ""),
        key=f"{prefix}-main",
        language_mix=language_mix,
    )
    for i, alt in enumerate(response.get("alternatives", [])):
        title = alt.get("title", "")
        content = alt.get("content", "")
        comparison = alt.get("comparison", "")
        body = f"**{title}**\n{content}\n_Comparison: {comparison}_"
        render_text_block(
            f"Alternative {i + 1}",
            body,
            key=f"{prefix}-alt-{i}",
            language_mix=language_mix,
        )
    render_text_block(
        "Strategic Reasoning",
        response.get("strategic_reasoning", ""),
        key=f"{prefix}-strategy",
        language_mix=language_mix,
    )
    render_text_block(
        "Execution Tips",
        response.get("execution_tips", ""),
        key=f"{prefix}-tips",
        language_mix=language_mix,
    )
    render_text_block(
        "Follow-up Question",
        response.get("follow_up_question", ""),
        key=f"{prefix}-followup",
        language_mix=language_mix,
    )


def render_api_error(exc: Exception) -> None:
    st.error(str(exc))
