"""Reusable Streamlit UI components — cream & coffee theme."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from app.ui.text_utils import should_use_rtl

# (material_symbol_name, display_label)
NAV_OPTIONS: dict[str, tuple[str, str]] = {
    "setup": ("tune", "Setup"),
    "chat": ("forum", "Chat"),
    "content": ("edit_note", "Content"),
    "networking": ("groups", "Networking"),
    "profile": ("badge", "Profile"),
    "advisor": ("light_mode", "Advisor"),
    "strategy": ("track_changes", "Strategy"),
}

DISCLAIMER_FA = (
    "<strong>LinkAid فقط پیشنهاد می‌دهد</strong> — هیچ پست، پیام یا اقدامی به‌صورت خودکار "
    "در لینکدین انجام نمی‌شود. شما تصمیم نهایی را می‌گیرید."
)
DISCLAIMER_EN = (
    "<strong>Suggest-only</strong> — LinkAid never posts, sends messages, or takes "
    "automated actions on LinkedIn. You decide what to use."
)

THEME_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=swap');

:root {
  --cream: #FAF6F1;
  --cream-dark: #F0E8DE;
  --coffee: #6F4E37;
  --coffee-dark: #4A3222;
  --tan: #C4A77D;
  --espresso: #3D2914;
  --card: #FFFCF7;
  --border: #E8DDD0;
}

html, body, [class*="css"] {
  font-family: 'DM Sans', system-ui, sans-serif;
  color: var(--espresso);
}

.stApp {
  background: linear-gradient(180deg, var(--cream) 0%, #F5EDE3 100%);
}

.block-container {
  padding-top: 1.5rem;
  max-width: 1080px;
}

.material-symbols-outlined {
  font-family: 'Material Symbols Outlined';
  font-weight: normal;
  font-style: normal;
  font-size: 1.15rem;
  line-height: 1;
  vertical-align: middle;
  margin-right: 0.35rem;
}

.linkaid-hero {
  background: linear-gradient(135deg, var(--coffee) 0%, var(--coffee-dark) 100%);
  color: #FFF9F2;
  border-radius: 20px;
  padding: 1.6rem 2rem;
  margin-bottom: 1.25rem;
  box-shadow: 0 12px 32px rgba(74, 50, 34, 0.18);
  border: 1px solid rgba(255, 249, 242, 0.12);
}

.linkaid-hero h1 {
  font-family: 'Cormorant Garamond', Georgia, serif;
  margin: 0 0 0.4rem 0;
  font-size: 2.1rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.linkaid-hero p {
  margin: 0;
  opacity: 0.9;
  font-size: 0.98rem;
}

.linkaid-disclaimer {
  background: var(--card);
  border: 1px solid var(--tan);
  border-radius: 12px;
  padding: 0.8rem 1rem;
  margin-bottom: 1rem;
  font-size: 0.92rem;
  color: var(--coffee-dark);
}

.linkaid-rtl {
  direction: rtl;
  text-align: right;
  unicode-bidi: plaintext;
}

.linkaid-response-block {
  background: var(--card);
  border: 1px solid var(--border);
  border-left: 4px solid var(--coffee);
  padding: 0.9rem 1.1rem;
  border-radius: 0 12px 12px 0;
  margin: 0.35rem 0 0.85rem 0;
  white-space: pre-wrap;
  line-height: 1.6;
}

.linkaid-chat-bubble {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1rem 1.15rem;
  margin: 0.5rem 0;
  line-height: 1.65;
  box-shadow: 0 2px 10px rgba(61, 41, 20, 0.05);
}

.linkaid-chat-followup {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px dashed var(--border);
  font-size: 0.92rem;
  color: var(--coffee);
}

.linkaid-section-title {
  font-family: 'Cormorant Garamond', Georgia, serif;
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--coffee-dark);
  margin: 0.75rem 0 0.25rem 0;
}

[data-testid="stSidebar"] {
  background: var(--card);
  border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] h3 {
  font-family: 'Cormorant Garamond', Georgia, serif;
  color: var(--coffee-dark);
}

div[data-testid="stForm"] {
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1rem;
  background: var(--card);
}

.stButton > button[kind="primary"] {
  background: var(--coffee) !important;
  border-color: var(--coffee) !important;
  color: #FFF9F2 !important;
}

.stButton > button[kind="primary"]:hover {
  background: var(--coffee-dark) !important;
  border-color: var(--coffee-dark) !important;
}
"""


def inject_global_styles() -> None:
    st.markdown(f"<style>{THEME_CSS}</style>", unsafe_allow_html=True)


def icon_html(name: str) -> str:
    return f'<span class="material-symbols-outlined">{html.escape(name)}</span>'


def render_brand_header(title: str, subtitle: str, icon: str = "hub") -> None:
    st.markdown(
        f"""
        <div class="linkaid-hero">
          <h1>{icon_html(icon)}{html.escape(title)}</h1>
          <p>{html.escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def nav_label(page_key: str) -> str:
    _icon, label = NAV_OPTIONS[page_key]
    return label


def render_disclaimer(language_mix: str = "fa-en") -> None:
    text = DISCLAIMER_FA if language_mix == "fa-en" else DISCLAIMER_EN
    rtl = should_use_rtl(text, language_mix)
    cls = "linkaid-disclaimer linkaid-rtl" if rtl else "linkaid-disclaimer"
    st.markdown(
        f'<div class="{cls}">{icon_html("info")} {text}</div>',
        unsafe_allow_html=True,
    )


def copy_button(label: str, text: str, key: str) -> None:
    if hasattr(st, "copy_button"):
        st.copy_button(label, text, key=key)
    else:
        st.download_button(label, text, file_name=f"{key}.txt", key=key)


def render_text_block(title: str, text: str, *, key: str, language_mix: str = "fa-en") -> None:
    if not text:
        return
    rtl = should_use_rtl(text, language_mix)
    cls = "linkaid-response-block linkaid-rtl" if rtl else "linkaid-response-block"
    st.markdown(f'<div class="linkaid-section-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="{cls}">{html.escape(text)}</div>',
        unsafe_allow_html=True,
    )
    copy_button("Copy", text, key=key)


def render_chat_response(response: dict[str, Any], *, language_mix: str = "fa-en") -> None:
    """Compact chat view — main answer first, details collapsed."""
    main = response.get("main_recommendation", "")
    understanding = response.get("understanding", "")
    follow_up = response.get("follow_up_question", "")
    rtl = should_use_rtl(main or understanding, language_mix)
    cls = "linkaid-chat-bubble linkaid-rtl" if rtl else "linkaid-chat-bubble"

    body = main or understanding
    if understanding and main and understanding != main:
        body = f"{understanding}\n\n{main}"

    st.markdown(f'<div class="{cls}">{html.escape(body)}</div>', unsafe_allow_html=True)

    tips = response.get("execution_tips", "")
    reasoning = response.get("strategic_reasoning", "")
    if tips or reasoning:
        with st.expander("جزئیات بیشتر / More detail", expanded=False):
            if reasoning:
                st.markdown(f"**Strategy:** {reasoning}")
            if tips:
                st.markdown(f"**Tips:** {tips}")
            alts = response.get("alternatives", [])
            for i, alt in enumerate(alts):
                st.markdown(f"**{alt.get('title', f'Alt {i+1}')}:** {alt.get('content', '')}")

    if follow_up:
        fu_cls = "linkaid-chat-followup linkaid-rtl" if should_use_rtl(follow_up, language_mix) else "linkaid-chat-followup"
        st.markdown(
            f'<div class="{fu_cls}">{icon_html("help")} {html.escape(follow_up)}</div>',
            unsafe_allow_html=True,
        )

    if main:
        copy_button("Copy answer", main, key=f"chat-copy-{hash(main) % 10**8}")


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
        body = f"{title}\n{content}\nComparison: {comparison}"
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
