"""Tests for Streamlit UI helpers (no Streamlit runtime required)."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.ui.api_client import LinkAidAPIError, LinkAidClient
from app.ui.text_utils import contains_rtl_text, should_use_rtl


def test_contains_rtl_text():
    assert contains_rtl_text("سلام دنیا")
    assert contains_rtl_text("Hello سلام")
    assert not contains_rtl_text("Hello world")


def test_should_use_rtl_mixed_content():
    assert should_use_rtl("متن فارسی", "fa-en")
    assert not should_use_rtl("English only", "fa-en")
    assert not should_use_rtl("English only", "en")


def test_client_health_success():
    client = LinkAidClient(base_url="http://testserver")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok", "app": "LinkAid", "version": "0.1.0"}

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.request.return_value = mock_response
        mock_client_cls.return_value = mock_client

        data = client.health()

    assert data["status"] == "ok"


def test_client_connect_error():
    client = LinkAidClient(base_url="http://localhost:9999")

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.request.side_effect = httpx.ConnectError("failed")
        mock_client_cls.return_value = mock_client

        with pytest.raises(LinkAidAPIError, match="Cannot reach API"):
            client.health()


def test_client_api_error_message():
    client = LinkAidClient(base_url="http://testserver")
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "internal"
    mock_response.json.return_value = {"message": "Agent error: no key"}

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.request.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with pytest.raises(LinkAidAPIError, match="Agent error"):
            client.chat("hi", thread_id="t1", user_id="u1")
