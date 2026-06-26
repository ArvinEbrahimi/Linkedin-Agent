from fastapi import APIRouter

from app.config import get_settings
from app.models.responses import ReadyResponse

router = APIRouter(tags=["health"])


@router.get(
    "/ready",
    response_model=ReadyResponse,
    summary="Setup readiness checklist",
    description=(
        "Shows whether Groq and LinkedIn OAuth are configured. "
        "Use from the UI setup tab before first use."
    ),
)
async def readiness_check() -> ReadyResponse:
    settings = get_settings()
    groq_ok = settings.groq_configured
    linkedin_ok = settings.linkedin_oauth_configured

    checks = {
        "groq_api_key": groq_ok,
        "linkedin_oauth": linkedin_ok,
    }
    messages: list[str] = []
    if not groq_ok:
        messages.append("Set GROQ_API_KEY in .env for AI suggestions.")
    if not linkedin_ok:
        messages.append(
            "Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET for one-click LinkedIn login."
        )
    if not messages:
        messages.append("All core integrations configured.")

    if groq_ok and linkedin_ok:
        status = "ready"
    elif groq_ok:
        status = "degraded"
    else:
        status = "not_ready"

    return ReadyResponse(
        status=status,
        groq_configured=groq_ok,
        linkedin_oauth_configured=linkedin_ok,
        checks=checks,
        messages=messages,
    )
