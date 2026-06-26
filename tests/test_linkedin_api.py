"""Tests for /ready and LinkedIn API routes."""

import io
import zipfile
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.models.linkedin import LinkedInImportResult
from app.services.linkedin import LinkedInService


@pytest.mark.asyncio
async def test_ready_endpoint():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert "groq_configured" in data
    assert "checks" in data
    assert data["status"] in ("ready", "degraded", "not_ready")


@pytest.mark.asyncio
async def test_linkedin_import_api():
    mock_linkedin = MagicMock(spec=LinkedInService)
    mock_linkedin.import_data_export = MagicMock(
        return_value=LinkedInImportResult(
            user_id="u1",
            posts_imported=2,
            profile_fields_updated=["linkedin_headline"],
            headline="Engineer",
            message="Imported 2 posts.",
        )
    )

    app = create_app()
    app.state.linkedin_service = mock_linkedin
    app.state.graph = MagicMock()
    app.state.content_service = MagicMock()
    app.state.networking_service = MagicMock()
    app.state.profile_service = MagicMock()
    app.state.memory_service = MagicMock()
    app.state.advisor_service = MagicMock()
    app.state.strategy_service = MagicMock()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("Shares.csv", "ShareCommentary\nHello world post\n")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/linkedin/import/u1",
            files={"file": ("export.zip", buf.getvalue(), "application/zip")},
        )

    assert response.status_code == 200
    assert response.json()["posts_imported"] == 2
