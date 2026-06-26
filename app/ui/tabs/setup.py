"""Setup, LinkedIn connect, and data import tab."""

from __future__ import annotations

import streamlit as st

from app.ui.api_client import LinkAidAPIError, LinkAidClient
from app.ui.components import render_api_error


def render_setup_tab(client: LinkAidClient, user_id: str) -> None:
    st.subheader("Setup & LinkedIn")
    st.caption(
        "۱) Groq API key برای پیشنهادهای AI  "
        "۲) اتصال LinkedIn  "
        "۳) import فایل export"
    )

    _render_readiness(client)
    st.divider()
    _render_linkedin_connect(client, user_id)
    st.divider()
    _render_import(client, user_id)


def _render_readiness(client: LinkAidClient) -> None:
    st.markdown("**۱ — AI readiness (Groq)**")
    try:
        ready = client.ready()
        health = client.health()
    except LinkAidAPIError as exc:
        render_api_error(exc)
        return

    if ready.get("groq_configured"):
        st.success("GROQ_API_KEY configured — content, chat, and strategy are ready.")
    else:
        st.error("GROQ_API_KEY missing on the API server.")
        st.code(
            "# In .env on the machine running `make run`:\nGROQ_API_KEY=your_key_here",
            language="bash",
        )

    for msg in ready.get("messages", []):
        st.caption(msg)

    st.caption(
        f"API: {health.get('app')} v{health.get('version')} · env={health.get('env')}"
    )


def _render_linkedin_connect(client: LinkAidClient, user_id: str) -> None:
    st.markdown("**۲ — Connect LinkedIn (read-only OAuth)**")
    st.caption(
        "Sign In with LinkedIn gives name and email only — no auto-posting. "
        "Register your app at linkedin.com/developers (see docs/LINKEDIN_SETUP.md)."
    )

    try:
        status = client.linkedin_status(user_id)
    except LinkAidAPIError as exc:
        render_api_error(exc)
        return

    if status.get("connected"):
        st.success(f"Connected as **{status.get('name') or status.get('linkedin_sub')}**")
        if status.get("email"):
            st.caption(status["email"])
        if st.button("Disconnect LinkedIn", type="secondary"):
            try:
                client.linkedin_disconnect(user_id)
                st.rerun()
            except LinkAidAPIError as exc:
                render_api_error(exc)
        return

    try:
        auth = client.linkedin_auth_url(user_id)
    except LinkAidAPIError as exc:
        if "not configured" in str(exc).lower():
            st.warning("LinkedIn OAuth not configured on server.")
            st.code(
                "LINKEDIN_CLIENT_ID=...\nLINKEDIN_CLIENT_SECRET=...\n"
                "LINKEDIN_REDIRECT_URI=http://localhost:8000/api/v1/linkedin/auth/callback",
                language="bash",
            )
        else:
            render_api_error(exc)
        return

    st.link_button("🔗 Connect LinkedIn", auth["auth_url"], type="primary")
    st.caption("Opens LinkedIn login — you'll return to LinkAid automatically.")


def _render_import(client: LinkAidClient, user_id: str) -> None:
    st.markdown("**۳ — Import LinkedIn data export**")
    st.caption(
        "LinkedIn → Settings → Data privacy → **Get a copy of your data** → "
        "Request archive → upload the ZIP here. Imports posts + headline/summary into memory."
    )

    uploaded = st.file_uploader("LinkedIn export (.zip)", type=["zip"])
    if st.button("Import into LinkAid", type="primary", disabled=uploaded is None):
        if uploaded is None:
            return
        with st.spinner("Parsing export…"):
            try:
                result = client.linkedin_import(user_id, uploaded.getvalue(), uploaded.name)
            except LinkAidAPIError as exc:
                render_api_error(exc)
                return

        st.success(result.get("message", "Import complete"))
        if result.get("headline"):
            st.info(f"Headline: {result['headline']}")
        if result.get("posts_imported", 0) > 0:
            st.session_state.onboarding_complete = True
            st.caption("Profile memory updated — advisor and strategy will use imported posts.")
