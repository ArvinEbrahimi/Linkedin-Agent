"""Login and registration screen."""

from __future__ import annotations

import streamlit as st

from app.ui.api_client import LinkAidAPIError, LinkAidClient
from app.ui.components import icon_html, render_brand_header


def render_auth_gate(client: LinkAidClient) -> bool:
    """Return True when the user is authenticated."""
    if st.session_state.get("access_token"):
        client.set_token(st.session_state.access_token)
        return True

    render_brand_header(
        "LinkAid",
        "دستیار برندسازی لینکدین برای مهندسان نرم‌افزار",
        icon="hub",
    )

    tab_login, tab_register = st.tabs(["ورود", "ثبت‌نام"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("ایمیل", placeholder="you@example.com")
            password = st.text_input("رمز عبور", type="password")
            submit = st.form_submit_button("ورود", type="primary", use_container_width=True)
        if submit:
            _handle_login(client, email, password)

    with tab_register:
        with st.form("register_form"):
            name = st.text_input("نام نمایشی")
            email = st.text_input("ایمیل", key="reg_email")
            password = st.text_input("رمز عبور (حداقل ۸ کاراکتر)", type="password", key="reg_pass")
            submit_reg = st.form_submit_button("ساخت اکانت", type="primary", use_container_width=True)
        if submit_reg:
            _handle_register(client, name, email, password)

    st.markdown(
        f'<p style="color:#6F4E37;font-size:0.9rem;">{icon_html("database")}'
        " پروفایل و تاریخچه چت در دیتابیس ذخیره می‌شود.</p>",
        unsafe_allow_html=True,
    )
    return bool(st.session_state.get("access_token"))


def _apply_auth(data: dict) -> None:
    st.session_state.access_token = data["access_token"]
    st.session_state.user_id = data["user_id"]
    st.session_state.display_name = data.get("display_name", "")
    st.session_state.user_email = data.get("email", "")
    st.session_state.onboarding_complete = False
    st.session_state.onboarding_step = 0
    st.rerun()


def _handle_login(client: LinkAidClient, email: str, password: str) -> None:
    if not email or not password:
        st.warning("ایمیل و رمز عبور را وارد کنید.")
        return
    try:
        data = client.login(email.strip(), password)
        client.set_token(data["access_token"])
        _apply_auth(data)
    except LinkAidAPIError as exc:
        st.error(str(exc))


def _handle_register(client: LinkAidClient, name: str, email: str, password: str) -> None:
    if not name or not email or not password:
        st.warning("همه فیلدها الزامی است.")
        return
    try:
        data = client.register(email.strip(), password, name.strip())
        client.set_token(data["access_token"])
        _apply_auth(data)
    except LinkAidAPIError as exc:
        st.error(str(exc))


def render_logout_button() -> None:
    if st.sidebar.button("خروج", use_container_width=True):
        for key in (
            "access_token",
            "user_id",
            "display_name",
            "user_email",
            "onboarding_complete",
            "onboarding_step",
            "chat_history",
        ):
            st.session_state.pop(key, None)
        st.rerun()
