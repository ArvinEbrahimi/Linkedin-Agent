"""LinkAid Streamlit UI — suggest-only LinkedIn personal branding assistant."""

from __future__ import annotations

import os
import uuid

import streamlit as st

from app.ui.api_client import LinkAidAPIError, LinkAidClient
from app.ui.components import inject_global_styles, render_disclaimer
from app.ui.onboarding import render_onboarding
from app.ui.tabs.advisor import render_advisor_tab
from app.ui.tabs.chat import render_chat_tab
from app.ui.tabs.content import render_content_tab
from app.ui.tabs.networking import render_networking_tab
from app.ui.tabs.profile import render_profile_tab
from app.ui.tabs.setup import render_setup_tab
from app.ui.tabs.strategy import render_strategy_tab

st.set_page_config(
    page_title="LinkAid",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _init_session() -> None:
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"user-{str(uuid.uuid4())[:8]}"
    if "language_mix" not in st.session_state:
        st.session_state.language_mix = "fa-en"

    params = st.query_params
    if params.get("linkedin") == "connected":
        linked_user = params.get("user_id")
        if linked_user:
            st.session_state.user_id = linked_user
        st.session_state.linkedin_just_connected = True
        st.query_params.clear()


def _render_sidebar() -> LinkAidClient:
    st.sidebar.title("🔗 LinkAid")
    st.sidebar.caption("Personal branding assistant for Iranian software engineers")

    if "api_url" not in st.session_state:
        st.session_state.api_url = os.getenv("LINKAID_API_URL", "http://localhost:8000")

    st.sidebar.text_input(
        "API URL",
        key="api_url",
        help="FastAPI backend — run `make run` in another terminal",
    )
    client = LinkAidClient(base_url=st.session_state.api_url)

    st.sidebar.text_input("User ID", key="user_id")
    st.sidebar.selectbox(
        "UI language mix",
        ["fa-en", "en"],
        key="language_mix",
    )

    try:
        health = client.health()
        ready = client.ready()
        status_line = f"API online — {health.get('app')} v{health.get('version')}"
        if not ready.get("groq_configured"):
            st.sidebar.warning("Groq not configured — set GROQ_API_KEY")
        else:
            st.sidebar.success(status_line)
    except LinkAidAPIError as exc:
        st.sidebar.error(str(exc))

    try:
        li = client.linkedin_status(st.session_state.user_id)
        if li.get("connected"):
            st.sidebar.caption(f"LinkedIn: {li.get('name', 'connected')}")
    except LinkAidAPIError:
        pass

    if st.sidebar.button("Reset onboarding"):
        st.session_state.onboarding_complete = False
        st.session_state.onboarding_step = 0
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "**Modules:** Chat · Content · Networking · Profile · Advisor · Strategy"
    )
    return client


def main() -> None:
    _init_session()
    inject_global_styles()

    client = _render_sidebar()
    user_id = st.session_state.user_id
    language_mix = st.session_state.language_mix
    render_disclaimer(language_mix)

    if st.session_state.get("linkedin_just_connected"):
        st.success("LinkedIn connected — complete onboarding or import your data export.")
        st.session_state.linkedin_just_connected = False

    if render_onboarding(client, user_id):
        with st.expander("Or connect LinkedIn / import data first", expanded=False):
            render_setup_tab(client, user_id)
        return

    tab_setup, tab_chat, tab_content, tab_net, tab_prof, tab_advisor, tab_strategy = st.tabs(
        [
            "⚙️ Setup",
            "💬 Chat",
            "📝 Content",
            "🤝 Networking",
            "👤 Profile",
            "☀️ Advisor",
            "🎯 Strategy",
        ]
    )

    with tab_setup:
        render_setup_tab(client, user_id)

    with tab_chat:
        render_chat_tab(client, user_id, language_mix)

    with tab_content:
        render_content_tab(client, language_mix)

    with tab_net:
        render_networking_tab(client, user_id, language_mix)

    with tab_prof:
        render_profile_tab(client, language_mix)

    with tab_advisor:
        render_advisor_tab(client, user_id, language_mix)

    with tab_strategy:
        render_strategy_tab(client, user_id, language_mix)


if __name__ == "__main__":
    main()
