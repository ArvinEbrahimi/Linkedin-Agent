import pytest
from pydantic import ValidationError

from app.models.responses import AlternativeOption, LinkAidResponse
from app.models.user import UserConstraints, UserProfile


def test_linkaid_response_valid():
    response = LinkAidResponse(
        understanding="You want a LinkedIn post about AI agents.",
        main_recommendation="Hook: 90% of AI demos fail in production...",
        alternatives=[
            AlternativeOption(
                title="Story-driven",
                content="Last month I shipped an agent that...",
                comparison="More personal, higher comment rate",
            )
        ],
        strategic_reasoning="Document posts get highest saves in 2026.",
        execution_tips="Post Tuesday 9am Tehran time. Put link in first comment.",
        follow_up_question="What niche should we target — fintech or dev tools?",
    )
    assert len(response.alternatives) == 1


def test_linkaid_response_rejects_too_many_alternatives():
    alt = AlternativeOption(title="A", content="B", comparison="C")
    with pytest.raises(ValidationError):
        LinkAidResponse(
            understanding="x",
            main_recommendation="y",
            alternatives=[alt, alt, alt, alt],
            strategic_reasoning="z",
            execution_tips="t",
            follow_up_question="q",
        )


def test_user_profile_defaults():
    profile = UserProfile()
    assert profile.constraints.iranian_market is True
    assert profile.constraints.max_daily_connections == 20
    assert profile.language_mix == "fa-en"


def test_user_constraints_max_connections_capped():
    with pytest.raises(ValidationError):
        UserConstraints(max_daily_connections=25)
