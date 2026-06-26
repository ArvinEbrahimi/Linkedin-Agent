"""First-run profile onboarding wizard."""

from __future__ import annotations

import streamlit as st

from app.ui.api_client import LinkAidAPIError, LinkAidClient
from app.ui.components import render_api_error


def _profile_needs_onboarding(client: LinkAidClient, user_id: str) -> bool:
    if st.session_state.get("onboarding_complete"):
        return False
    try:
        data = client.get_profile(user_id)
        profile = data.get("profile")
        if profile and profile.get("niche"):
            st.session_state.onboarding_complete = True
            if profile.get("language_mix"):
                st.session_state.language_mix = profile["language_mix"]
            return False
        return True
    except LinkAidAPIError:
        return True


def _prefill_from_linkedin(client: LinkAidClient, user_id: str) -> None:
    if st.session_state.get("ob_prefilled"):
        return
    try:
        status = client.linkedin_status(user_id)
        if status.get("connected") and status.get("name"):
            st.session_state.ob_name = status["name"]
        profile = client.get_profile(user_id).get("profile") or {}
        if profile.get("linkedin_headline") and not st.session_state.get("ob_niche"):
            st.session_state.ob_niche = profile["linkedin_headline"]
        st.session_state.ob_prefilled = True
    except LinkAidAPIError:
        pass


def render_onboarding(client: LinkAidClient, user_id: str) -> bool:
    """Render wizard. Returns True when onboarding is still required."""
    if not _profile_needs_onboarding(client, user_id):
        return False

    _prefill_from_linkedin(client, user_id)

    st.subheader("👋 Welcome to LinkAid")
    st.caption(
        "چند سوال کوتاه تا پیشنهادهای شخصی‌سازی‌شده بگیرید. "
        "Welcome — tell us about your LinkedIn brand."
    )

    if "onboarding_step" not in st.session_state:
        st.session_state.onboarding_step = 0

    step = st.session_state.onboarding_step
    progress = (step + 1) / 4
    st.progress(progress, text=f"Step {step + 1} of 4")

    with st.form("onboarding_form"):
        if step == 0:
            st.markdown("**Step 1 — About you**")
            name = st.text_input("Name / نام", value=st.session_state.get("ob_name", ""))
            role = st.selectbox(
                "Role",
                ["Backend", "FullStack", "AI Engineer"],
                index=["Backend", "FullStack", "AI Engineer"].index(
                    st.session_state.get("ob_role", "Backend")
                ),
            )
            years = st.number_input(
                "Years of experience",
                min_value=0,
                max_value=40,
                value=st.session_state.get("ob_years", 3),
            )
        elif step == 1:
            st.markdown("**Step 2 — Niche & stack**")
            niche = st.text_area(
                "Your niche (e.g. LLM agents for fintech)",
                value=st.session_state.get("ob_niche", ""),
                placeholder="حوزه تخصصی شما در لینکدین",
            )
            tech_stack = st.text_input(
                "Tech stack (comma-separated)",
                value=st.session_state.get("ob_tech", "Python, FastAPI"),
            )
            goals = st.text_input(
                "Goals (comma-separated)",
                value=st.session_state.get("ob_goals", "remote jobs, thought leadership"),
            )
        elif step == 2:
            st.markdown("**Step 3 — Style**")
            tone = st.selectbox(
                "Tone",
                ["professional", "warm", "bold"],
                index=["professional", "warm", "bold"].index(
                    st.session_state.get("ob_tone", "professional")
                ),
            )
            language_mix = st.selectbox("Language mix", ["fa-en", "en"])
            posting_frequency = st.selectbox(
                "Posting frequency",
                ["1-2/week", "2-5/week", "5+/week"],
                index=1,
            )
            target_audience = st.text_input(
                "Target audience (comma-separated)",
                value=st.session_state.get("ob_audience", "CTOs, engineering leads"),
            )
        else:
            st.markdown("**Step 4 — Competitors (optional)**")
            st.text_input(
                "Competitor names or profiles (comma-separated)",
                value=st.session_state.get("ob_competitors", ""),
                key="ob_competitors_input",
            )
            st.info("You can skip competitors and add them later in Strategy tab.")

        col_back, col_next = st.columns(2)
        back = col_back.form_submit_button("← Back", disabled=step == 0)
        nxt = col_next.form_submit_button("Next →" if step < 3 else "Finish ✓")

    if back and step > 0:
        st.session_state.onboarding_step = step - 1
        st.rerun()

    if nxt:
        if step == 0:
            st.session_state.ob_name = name
            st.session_state.ob_role = role
            st.session_state.ob_years = years
            st.session_state.onboarding_step = 1
            st.rerun()
        if step == 1:
            if not niche or len(niche.strip()) < 3:
                st.warning("Please enter your niche (حداقل ۳ کاراکتر).")
                return True
            st.session_state.ob_niche = niche
            st.session_state.ob_tech = tech_stack
            st.session_state.ob_goals = goals
            st.session_state.onboarding_step = 2
            st.rerun()
        if step == 2:
            st.session_state.ob_tone = tone
            st.session_state.ob_language = language_mix
            st.session_state.ob_frequency = posting_frequency
            st.session_state.ob_audience = target_audience
            st.session_state.onboarding_step = 3
            st.rerun()
        if step == 3:
            st.session_state.ob_competitors = st.session_state.get("ob_competitors_input", "")
            _save_onboarding_profile(client, user_id)
            return False

    return True


def _save_onboarding_profile(client: LinkAidClient, user_id: str) -> None:
    def split_csv(value: str) -> list[str]:
        return [p.strip() for p in value.split(",") if p.strip()]

    profile = {
        "name": st.session_state.get("ob_name"),
        "role": st.session_state.get("ob_role"),
        "years_experience": st.session_state.get("ob_years"),
        "niche": st.session_state.get("ob_niche"),
        "tech_stack": split_csv(st.session_state.get("ob_tech", "")),
        "goals": split_csv(st.session_state.get("ob_goals", "")),
        "tone_preference": st.session_state.get("ob_tone", "professional"),
        "language_mix": st.session_state.get("ob_language", "fa-en"),
        "posting_frequency": st.session_state.get("ob_frequency", "2-5/week"),
        "target_audience": split_csv(st.session_state.get("ob_audience", "")),
        "competitors": split_csv(st.session_state.get("ob_competitors", "")),
        "constraints": {"iranian_market": True, "max_daily_connections": 20},
    }
    try:
        client.save_profile(user_id, profile)
        st.session_state.onboarding_complete = True
        st.session_state.language_mix = profile["language_mix"]
        st.success("Profile saved! پروفایل ذخیره شد — let's build your brand.")
        st.session_state.onboarding_step = 0
        st.rerun()
    except LinkAidAPIError as exc:
        render_api_error(exc)
