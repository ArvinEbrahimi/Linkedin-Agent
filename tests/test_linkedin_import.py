"""Tests for LinkedIn data export import."""

import csv
import io
import zipfile

from app.services.linkedin_import import parse_linkedin_export_zip


def _build_sample_zip() -> bytes:
    buf = io.BytesIO()
    profile_csv = io.StringIO()
    writer = csv.DictWriter(profile_csv, fieldnames=["Headline", "Summary"])
    writer.writeheader()
    writer.writerow(
        {
            "Headline": "Senior Backend Engineer | Python & FastAPI",
            "Summary": "I build scalable APIs for remote teams.",
        }
    )

    shares_csv = io.StringIO()
    writer2 = csv.DictWriter(shares_csv, fieldnames=["ShareCommentary", "ShareDate", "MediaType"])
    writer2.writeheader()
    writer2.writerow(
        {
            "ShareCommentary": "Three lessons from shipping LLM agents to production.",
            "ShareDate": "2025-01-15 10:00:00",
            "MediaType": "TEXT",
        }
    )
    writer2.writerow(
        {
            "ShareCommentary": "Short post",
            "ShareDate": "2025-01-10",
            "MediaType": "VIDEO",
        }
    )

    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("Profile.csv", profile_csv.getvalue())
        zf.writestr("Shares.csv", shares_csv.getvalue())
    return buf.getvalue()


def test_parse_linkedin_export_zip():
    payload = parse_linkedin_export_zip(_build_sample_zip())
    assert payload.headline == "Senior Backend Engineer | Python & FastAPI"
    assert "scalable APIs" in (payload.summary or "")
    assert len(payload.posts) == 2
    assert payload.posts[0].post_type == "text"
    assert payload.posts[1].post_type == "video"


def test_parse_empty_zip_raises_or_returns_empty():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w"):
        pass
    payload = parse_linkedin_export_zip(buf.getvalue())
    assert payload.posts == []
