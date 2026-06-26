"""Extension relies on these API routes — guard against accidental removal."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app

EXTENSION_PATHS = [
    "/api/v1/health",
    "/api/v1/ready",
    "/api/v1/networking/analyze",
    "/api/v1/content/post",
    "/api/v1/linkedin/status/{user_id}",
]


@pytest.mark.asyncio
async def test_extension_required_openapi_paths():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    for route in EXTENSION_PATHS:
        normalized = route.replace("{user_id}", "{user_id}")
        assert normalized in paths, f"Missing extension route: {route}"
