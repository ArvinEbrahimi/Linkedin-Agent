#!/usr/bin/env python3
"""E2E smoke test against a running LinkAid API.

Usage:
    # API must be running (make run or docker compose up)
    python scripts/e2e_smoke.py

    # Custom base URL
    LINKAID_BASE_URL=http://localhost:8000 python scripts/e2e_smoke.py

    # Also exercise chat (requires GROQ_API_KEY on server)
    python scripts/e2e_smoke.py --chat
"""

from __future__ import annotations

import argparse
import os
import sys

import httpx

DEFAULT_BASE_URL = "http://localhost:8000"
TIMEOUT = 120.0


def check_health(client: httpx.Client) -> None:
    response = client.get("/api/v1/health")
    response.raise_for_status()
    data = response.json()
    assert data.get("status") == "ok", data
    print(f"✓ health — {data.get('app')} v{data.get('version')} [{data.get('env')}]")


def check_openapi(client: httpx.Client) -> None:
    response = client.get("/openapi.json")
    response.raise_for_status()
    schema = response.json()
    paths = schema.get("paths", {})
    assert "/api/v1/health" in paths
    assert "/api/v1/chat" in paths
    print(f"✓ openapi — {len(paths)} paths documented")


def check_chat(client: httpx.Client) -> None:
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Write a short LinkedIn post about Python backend engineering.",
            "thread_id": "e2e-smoke",
            "user_id": "e2e-user",
        },
    )
    if response.status_code == 500:
        detail = response.json()
        if detail.get("error") == "configuration_error":
            print("⚠ chat skipped — GROQ_API_KEY not configured on server")
            return
    response.raise_for_status()
    data = response.json()
    assert "response" in data
    assert data["response"].get("main_recommendation")
    print(f"✓ chat — intent={data.get('intent')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="LinkAid E2E smoke test")
    parser.add_argument(
        "--base-url",
        default=os.getenv("LINKAID_BASE_URL", DEFAULT_BASE_URL),
        help="API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Also test POST /api/v1/chat (requires GROQ_API_KEY on server)",
    )
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    print(f"Smoke testing {base_url} …")
    try:
        with httpx.Client(base_url=base_url, timeout=TIMEOUT) as client:
            check_health(client)
            check_openapi(client)
            if args.chat:
                check_chat(client)
    except httpx.ConnectError:
        print(f"✗ Cannot connect to {base_url} — start API with: make run", file=sys.stderr)
        return 1
    except httpx.HTTPStatusError as exc:
        print(f"✗ HTTP {exc.response.status_code}: {exc.response.text}", file=sys.stderr)
        return 1
    except AssertionError as exc:
        print(f"✗ Assertion failed: {exc}", file=sys.stderr)
        return 1

    print("All smoke checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
