"""Streamlit session helpers — avoid widget-bound key conflicts."""

from __future__ import annotations

import streamlit as st

PENDING_LANGUAGE_MIX = "_pending_language_mix"
DEFAULT_LANGUAGE_MIX = "fa-en"


def apply_pending_session_updates() -> None:
    """Apply queued updates before widgets with matching keys are created."""
    if PENDING_LANGUAGE_MIX in st.session_state:
        value = st.session_state.pop(PENDING_LANGUAGE_MIX)
        st.session_state.language_mix = value
        st.session_state.ui_language_mix = value


def defer_language_mix(value: str) -> None:
    """Queue language sync for the next run (before sidebar mounts)."""
    st.session_state[PENDING_LANGUAGE_MIX] = value


def init_language_mix() -> None:
    """Initialize app language state (not bound to any widget key)."""
    apply_pending_session_updates()
    if "language_mix" not in st.session_state:
        st.session_state.language_mix = DEFAULT_LANGUAGE_MIX


def init_sidebar_language_widget() -> None:
    """Seed sidebar widget only when it has no value yet."""
    if "ui_language_mix" not in st.session_state:
        st.session_state.ui_language_mix = st.session_state.get(
            "language_mix", DEFAULT_LANGUAGE_MIX
        )


def sync_language_mix_from_sidebar() -> None:
    """Copy sidebar widget value into app language after sidebar renders."""
    st.session_state.language_mix = st.session_state.get(
        "ui_language_mix", DEFAULT_LANGUAGE_MIX
    )
