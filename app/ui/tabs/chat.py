"""Chat tab — multi-turn conversation with thread persistence."""

from __future__ import annotations

import uuid

import streamlit as st

from app.ui.api_client import LinkAidAPIError, LinkAidClient
from app.ui.components import render_api_error, render_chat_response


def _init_chat_state() -> None:
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())[:8]
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def render_chat_tab(client: LinkAidClient, user_id: str, language_mix: str) -> None:
    _init_chat_state()

    col_info, col_new = st.columns([4, 1])
    col_info.caption(f"Thread `{st.session_state.thread_id}` · history saved on server")
    if col_new.button("New thread", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())[:8]
        st.session_state.chat_history = []
        st.rerun()

    for entry in st.session_state.chat_history:
        with st.chat_message("user"):
            st.markdown(entry["message"])
        with st.chat_message("assistant"):
            intent = entry.get("intent", "general")
            st.caption(f"Intent: {intent}")
            render_chat_response(entry["response"], language_mix=language_mix)

    placeholder = (
        "سوالت را بپرس — مثلاً: از کجا شروع کنم برای بهتر کردن پروفایلم؟"
        if language_mix == "fa-en"
        else "Ask anything about your LinkedIn brand…"
    )
    prompt = st.chat_input(placeholder)
    if not prompt:
        return

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("در حال فکر کردن…" if language_mix == "fa-en" else "Thinking…"):
            try:
                data = client.chat(
                    prompt,
                    thread_id=st.session_state.thread_id,
                    user_id=user_id,
                )
            except LinkAidAPIError as exc:
                render_api_error(exc)
                return

        response = data["response"]
        st.caption(f"Intent: {data.get('intent', 'general')}")
        entry_id = len(st.session_state.chat_history)
        render_chat_response(response, language_mix=language_mix)
        st.session_state.chat_history.append(
            {
                "id": entry_id,
                "message": prompt,
                "intent": data.get("intent"),
                "response": response,
            }
        )
