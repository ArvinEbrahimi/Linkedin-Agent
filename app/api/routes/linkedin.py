import logging

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import HTMLResponse

from app.api.deps import get_linkedin_service
from app.config import get_settings
from app.core.exceptions import LinkAidError
from app.models.linkedin import (
    LinkedInAuthUrlResponse,
    LinkedInImportResult,
    LinkedInStatusResponse,
)
from app.services.linkedin import LinkedInService
from app.services.linkedin_oauth import LinkedInOAuthError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/linkedin", tags=["linkedin"])


@router.get(
    "/auth/url",
    response_model=LinkedInAuthUrlResponse,
    summary="Get LinkedIn OAuth URL",
    description=(
        "Start Sign In with LinkedIn (OpenID Connect). Open the returned URL in a browser. "
        "Requires LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET on the server."
    ),
)
async def linkedin_auth_url(
    user_id: str = Query(default="default"),
    linkedin_service: LinkedInService = Depends(get_linkedin_service),
) -> LinkedInAuthUrlResponse:
    auth_url, state = linkedin_service.oauth.create_auth_url(user_id)
    return LinkedInAuthUrlResponse(auth_url=auth_url, state=state)


@router.get(
    "/auth/callback",
    summary="LinkedIn OAuth callback",
    include_in_schema=False,
)
async def linkedin_auth_callback(
    code: str = Query(...),
    state: str = Query(...),
    linkedin_service: LinkedInService = Depends(get_linkedin_service),
) -> HTMLResponse:
    settings = get_settings()
    try:
        user_id, userinfo = await linkedin_service.oauth.handle_callback(code, state)
    except (LinkedInOAuthError, LinkAidError) as exc:
        return HTMLResponse(
            f"<h2>LinkedIn connection failed</h2><p>{exc.message}</p>",
            status_code=400,
        )

    ui_url = f"{settings.ui_base_url.rstrip('/')}/?linkedin=connected&user_id={user_id}"
    name = userinfo.name or "your account"
    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>LinkAid — LinkedIn Connected</title></head>
    <body style="font-family:sans-serif;max-width:520px;margin:3rem auto;padding:1rem;">
      <h2>✅ LinkedIn connected</h2>
      <p>Signed in as <strong>{name}</strong>. User ID: <code>{user_id}</code></p>
      <p><a href="{ui_url}">Return to LinkAid UI</a></p>
      <script>setTimeout(function(){{ window.location.href = "{ui_url}"; }}, 2500);</script>
    </body></html>
    """
    return HTMLResponse(html)


@router.get(
    "/status/{user_id}",
    response_model=LinkedInStatusResponse,
    summary="LinkedIn connection status",
)
async def linkedin_status(
    user_id: str,
    linkedin_service: LinkedInService = Depends(get_linkedin_service),
) -> LinkedInStatusResponse:
    return LinkedInStatusResponse.model_validate(linkedin_service.oauth.get_status(user_id))


@router.delete(
    "/disconnect/{user_id}",
    summary="Disconnect LinkedIn account",
)
async def linkedin_disconnect(
    user_id: str,
    linkedin_service: LinkedInService = Depends(get_linkedin_service),
) -> LinkedInStatusResponse:
    linkedin_service.oauth.disconnect(user_id)
    return LinkedInStatusResponse(user_id=user_id, connected=False)


@router.post(
    "/import/{user_id}",
    response_model=LinkedInImportResult,
    summary="Import LinkedIn data export ZIP",
    description=(
        "Upload the ZIP from LinkedIn Settings → Data privacy → "
        "Get a copy of your data. Imports posts and profile summary into memory."
    ),
)
async def linkedin_import(
    user_id: str,
    file: UploadFile = File(..., description="LinkedIn data export .zip"),
    linkedin_service: LinkedInService = Depends(get_linkedin_service),
) -> LinkedInImportResult:
    content = await file.read()
    return linkedin_service.import_data_export(user_id, content)
