"""HTTP client for the LinkAid FastAPI backend."""

from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_API_URL = "http://localhost:8000"


class LinkAidAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class LinkAidClient:
    def __init__(self, base_url: str | None = None, timeout: float = 120.0) -> None:
        self.base_url = (base_url or os.getenv("LINKAID_API_URL", DEFAULT_API_URL)).rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(method, url, **kwargs)
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

    def health(self) -> dict:
        return self._request("GET", "/api/v1/health")

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
