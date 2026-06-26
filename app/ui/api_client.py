"""HTTP client for the LinkAid FastAPI backend."""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

DEFAULT_API_URL = "http://localhost:8000"
STATUS_CACHE_TTL = 30.0


class LinkAidAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class LinkAidClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 120.0,
        access_token: str | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("LINKAID_API_URL", DEFAULT_API_URL)).rstrip("/")
        self.timeout = timeout
        self.access_token = access_token
        self._client: httpx.Client | None = None
        self._status_cache: dict[str, Any] | None = None
        self._status_cached_at: float = 0.0

    def set_token(self, token: str | None) -> None:
        self.access_token = token
        self.invalidate_status_cache()

    def _get_client(self) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            self._client.close()
        self._client = None

    def invalidate_status_cache(self) -> None:
        self._status_cache = None
        self._status_cached_at = 0.0

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        headers = {**self._headers(), **kwargs.pop("headers", {})}
        try:
            response = self._get_client().request(method, url, headers=headers, **kwargs)
        except httpx.ConnectError as exc:
            raise LinkAidAPIError(
                f"Cannot reach API at {self.base_url}. Start it with: make run"
            ) from exc
        except httpx.TimeoutException as exc:
            raise LinkAidAPIError("Request timed out — the agent may still be processing.") from exc

        if response.status_code >= 400:
            detail = response.text
            try:
                detail = response.json().get("message", detail)
            except Exception:
                pass
            raise LinkAidAPIError(detail, status_code=response.status_code)

        if response.status_code == 204:
            return None
        return response.json()

    def get_status_bundle(self, user_id: str, *, force: bool = False) -> dict[str, Any]:
        now = time.monotonic()
        if (
            not force
            and self._status_cache is not None
            and (now - self._status_cached_at) < STATUS_CACHE_TTL
        ):
            return self._status_cache

        bundle: dict[str, Any] = {"health": None, "ready": None, "linkedin": None}
        try:
            bundle["health"] = self.health()
            bundle["ready"] = self.ready()
        except LinkAidAPIError as exc:
            bundle["error"] = str(exc)
        try:
            bundle["linkedin"] = self.linkedin_status(user_id)
        except LinkAidAPIError:
            bundle["linkedin"] = None

        self._status_cache = bundle
        self._status_cached_at = now
        return bundle

    def register(self, email: str, password: str, display_name: str) -> dict:
        return self._request(
            "POST",
            "/api/v1/auth/register",
            json={"email": email, "password": password, "display_name": display_name},
        )

    def login(self, email: str, password: str) -> dict:
        return self._request(
            "POST",
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )

    def me(self) -> dict:
        return self._request("GET", "/api/v1/auth/me")

    def health(self) -> dict:
        return self._request("GET", "/api/v1/health")

    def ready(self) -> dict:
        return self._request("GET", "/api/v1/ready")

    def linkedin_auth_url(self, user_id: str) -> dict:
        return self._request("GET", f"/api/v1/linkedin/auth/url?user_id={user_id}")

    def linkedin_status(self, user_id: str) -> dict:
        return self._request("GET", f"/api/v1/linkedin/status/{user_id}")

    def linkedin_disconnect(self, user_id: str) -> dict:
        return self._request("DELETE", f"/api/v1/linkedin/disconnect/{user_id}")

    def linkedin_import(self, user_id: str, file_bytes: bytes, filename: str) -> dict:
        return self._request(
            "POST",
            f"/api/v1/linkedin/import/{user_id}",
            files={"file": (filename, file_bytes, "application/zip")},
        )

    def chat(self, message: str, *, thread_id: str, user_id: str) -> dict:
        return self._request(
            "POST",
            "/api/v1/chat",
            json={"message": message, "thread_id": thread_id, "user_id": user_id},
        )

    def get_profile(self, user_id: str) -> dict:
        return self._request("GET", f"/api/v1/memory/profile/{user_id}")

    def save_profile(self, user_id: str, profile: dict) -> dict:
        return self._request(
            "PUT",
            f"/api/v1/memory/profile/{user_id}",
            json={"profile": profile},
        )

    def generate_post(self, payload: dict) -> dict:
        return self._request("POST", "/api/v1/content/post", json=payload)

    def generate_campaign(self, payload: dict) -> dict:
        return self._request("POST", "/api/v1/content/campaign", json=payload)

    def analyze_profile(self, payload: dict) -> dict:
        return self._request("POST", "/api/v1/networking/analyze", json=payload)

    def generate_outreach(self, payload: dict) -> dict:
        return self._request("POST", "/api/v1/networking/outreach", json=payload)

    def optimize_profile(self, payload: dict) -> dict:
        return self._request("POST", "/api/v1/profile/optimize", json=payload)

    def morning_briefing(self, user_id: str) -> dict:
        return self._request("POST", "/api/v1/advisor/briefing", json={"user_id": user_id})

    def analyze_post(self, payload: dict) -> dict:
        return self._request("POST", "/api/v1/advisor/post-analysis", json=payload)

    def outreach_suggestions(self, user_id: str, max_suggestions: int = 10) -> dict:
        return self._request(
            "POST",
            "/api/v1/advisor/outreach",
            json={"user_id": user_id, "max_suggestions": max_suggestions},
        )

    def build_narrative(self, payload: dict) -> dict:
        return self._request("POST", "/api/v1/strategy/narrative", json=payload)

    def analyze_competitors(self, payload: dict) -> dict:
        return self._request("POST", "/api/v1/strategy/competitor", json=payload)

    def build_calendar(self, payload: dict) -> dict:
        return self._request("POST", "/api/v1/strategy/calendar", json=payload)
