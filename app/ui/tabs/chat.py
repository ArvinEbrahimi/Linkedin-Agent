"""Chat tab — multi-turn conversation with thread persistence."""

from __future__ import annotations

import uuid

import streamlit as st

from app.ui.api_client import LinkAidAPIError, LinkAidClient
from app.ui.components import render_api_error, render_linkaid_response


def _init_chat_state() -> None:
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())[:8]
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def render_chat_tab(client: LinkAidClient, user_id: str, language_mix: str) -> None:
    _init_chat_state()

    col_info, col_new = st.columns([4, 1])
    col_info.caption(f"Thread: `{st.session_state.thread_id}` — persisted via API checkpointer")
    if col_new.button("New thread", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())[:8]
        st.session_state.chat_history = []
        st.rerun()

    for entry in st.session_state.chat_history:
        with st.chat_message("user"):
            st.markdown(entry["message"])
        with st.chat_message("assistant"):
            st.caption(f"Intent: `{entry.get('intent', 'general')}`")
            render_linkaid_response(
                entry["response"],
                prefix=f"chat-{entry['id']}",
                language_mix=language_mix,
            )

    prompt = st.chat_input("Ask LinkAid anything about LinkedIn branding…")
    if not prompt:
        return

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
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
        st.caption(f"Intent: `{data.get('intent', 'general')}`")
        entry_id = len(st.session_state.chat_history)
        render_linkaid_response(
            response,
            prefix=f"chat-{entry_id}",
            language_mix=language_mix,
        )
        st.session_state.chat_history.append(
            {
                "id": entry_id,
                "message": prompt,
                "intent": data.get("intent"),
                "response": response,
            }
        )
