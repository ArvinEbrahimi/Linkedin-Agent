"""LinkAid Streamlit UI — suggest-only LinkedIn personal branding assistant."""

from __future__ import annotations

import os

import streamlit as st

from app.ui.api_client import LinkAidAPIError, LinkAidClient
from app.ui.auth_page import render_auth_gate, render_logout_button
from app.ui.components import NAV_OPTIONS, inject_global_styles, nav_label, render_brand_header, render_disclaimer
from app.ui.onboarding import render_onboarding
from app.ui.session_helpers import (
    init_language_mix,
    init_sidebar_language_widget,
    sync_language_mix_from_sidebar,
)
from app.ui.tabs.advisor import render_advisor_tab
from app.ui.tabs.chat import render_chat_tab
from app.ui.tabs.content import render_content_tab
from app.ui.tabs.networking import render_networking_tab
from app.ui.tabs.profile import render_profile_tab
from app.ui.tabs.setup import render_setup_tab
from app.ui.tabs.strategy import render_strategy_tab

st.set_page_config(
    page_title="LinkAid",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _init_session() -> None:
    init_language_mix()

    if "api_url" not in st.session_state:
        st.session_state.api_url = os.getenv("LINKAID_API_URL", "http://localhost:8000")

    if "active_page" not in st.session_state:
        st.session_state.active_page = "chat"

    params = st.query_params
    if params.get("linkedin") == "connected":
        linked_user = params.get("user_id")
        if linked_user and st.session_state.get("access_token"):
            if linked_user == st.session_state.get("user_id"):
                st.session_state.linkedin_just_connected = True
        st.query_params.clear()


def _make_client() -> LinkAidClient:
    return LinkAidClient(
        base_url=st.session_state.api_url,
        access_token=st.session_state.get("access_token"),
    )


def _render_sidebar(client: LinkAidClient, user_id: str) -> str:
    display = st.session_state.get("display_name") or "کاربر"
    email = st.session_state.get("user_email", "")
    st.sidebar.markdown(f"### {display}")
    if email:
        st.sidebar.caption(email)

    init_sidebar_language_widget()
    st.sidebar.selectbox(
        "زبان",
        ["fa-en", "en"],
        key="ui_language_mix",
        format_func=lambda x: "فارسی-انگلیسی" if x == "fa-en" else "English",
    )

    bundle = client.get_status_bundle(user_id)
    if bundle.get("error"):
        st.sidebar.error(bundle["error"])
    elif bundle.get("ready") and not bundle["ready"].get("groq_configured"):
        st.sidebar.warning("Groq تنظیم نشده")
    elif bundle.get("health"):
        health = bundle["health"]
        st.sidebar.success(f"Online · v{health.get('version')}")

    li = bundle.get("linkedin") or {}
    if li.get("connected"):
        st.sidebar.caption(f"LinkedIn · {li.get('name', 'connected')}")

    st.sidebar.markdown("---")
    page = st.sidebar.radio(
        "Navigation",
        options=list(NAV_OPTIONS.keys()),
        format_func=nav_label,
        key="active_page",
        label_visibility="collapsed",
    )

    if st.sidebar.button("Refresh status", use_container_width=True):
        client.invalidate_status_cache()
        st.rerun()

    if st.sidebar.button("Reset onboarding", use_container_width=True):
        st.session_state.onboarding_complete = False
        st.session_state.onboarding_step = 0
        st.rerun()

    render_logout_button()
    return page


def _page_icon(page: str) -> str:
    return NAV_OPTIONS.get(page, ("hub", ""))[0]


def _page_subtitle(page: str, language_mix: str) -> str:
    subtitles = {
        "chat": "گفتگوی هوشمند برای برندسازی لینکدین",
        "setup": "تنظیمات، LinkedIn و import داده",
        "content": "پیشنهاد پست و کمپین",
        "networking": "تحلیل و outreach",
        "profile": "بهینه‌سازی پروفایل",
        "advisor": "مشاور روزانه",
        "strategy": "استراتژی و برند",
    }
    if language_mix == "en":
        return "Your LinkedIn personal branding workspace"
    return subtitles.get(page, "فضای کار برندسازی لینکدین")


def _render_active_page(page: str, client: LinkAidClient, user_id: str, language_mix: str) -> None:
    if page == "setup":
        render_setup_tab(client, user_id)
    elif page == "chat":
        render_chat_tab(client, user_id, language_mix)
    elif page == "content":
        render_content_tab(client, language_mix)
    elif page == "networking":
        render_networking_tab(client, user_id, language_mix)
    elif page == "profile":
        render_profile_tab(client, language_mix)
    elif page == "advisor":
        render_advisor_tab(client, user_id, language_mix)
    elif page == "strategy":
        render_strategy_tab(client, user_id, language_mix)


def main() -> None:
    _init_session()
    inject_global_styles()

    client = _make_client()

    if not render_auth_gate(client):
        return

    user_id = st.session_state.user_id
    page = _render_sidebar(client, user_id)
    sync_language_mix_from_sidebar()
    language_mix = st.session_state.language_mix

    render_brand_header(
        nav_label(page),
        _page_subtitle(page, language_mix),
        icon=_page_icon(page),
    )
    render_disclaimer(language_mix)

    if st.session_state.pop("linkedin_just_connected", False):
        st.success("LinkedIn connected — complete onboarding or import your data export.")

    if render_onboarding(client, user_id):
        with st.expander("Connect LinkedIn or import data first", expanded=False):
            render_setup_tab(client, user_id)
        return

    _render_active_page(page, client, user_id, language_mix)


if __name__ == "__main__":
    main()
