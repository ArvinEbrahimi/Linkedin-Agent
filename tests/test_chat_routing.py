"""Chat routing and profile advisory tests."""

from langchain_core.messages import HumanMessage

from app.agents.graph import _route_after_classify
from app.services.profile import _is_profile_advisory, _infer_profile_section


def test_profile_intent_not_blocked_by_clarification_flag():
    state = {"intent": "profile", "needs_clarification": True}
    assert _route_after_classify(state) == "profile_agent"


def test_general_clarification_routes_to_generate_response():
    state = {"intent": "general", "needs_clarification": True}
    assert _route_after_classify(state) == "generate_response"


def test_content_intent_not_blocked_by_clarification():
    state = {"intent": "content", "needs_clarification": True}
    assert _route_after_classify(state) == "content_agent"


def test_is_profile_advisory_persian_question():
    assert _is_profile_advisory("خب بنظرت الان بهتره از کجا شروع کنم برای بهتر کردن پروفایلم؟")


def test_is_profile_advisory_not_long_paste():
    long_text = "x" * 300
    assert not _is_profile_advisory(long_text)


def test_infer_profile_section_headline():
    assert _infer_profile_section("optimize my headline please") == "headline"


def test_infer_profile_section_defaults_full():
    assert _infer_profile_section("improve everything") == "full"
