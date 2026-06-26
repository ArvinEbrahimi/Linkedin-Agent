"""Parse LinkedIn 'Get a copy of your data' export ZIP files."""

from __future__ import annotations

import csv
import io
import logging
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from app.models.user import PostRecord, UserProfile

PostType = Literal["text", "carousel", "video", "poll", "document"]

logger = logging.getLogger(__name__)

POST_FILE_HINTS = ("shares", "share", "posts", "ugcposts")
PROFILE_FILE_HINTS = ("profile summary", "profile.csv", "profile")
HEADLINE_COLUMNS = ("headline", "head line", "professional headline")
SUMMARY_COLUMNS = ("summary", "about", "about summary", "profile summary")
CONTENT_COLUMNS = (
    "sharecommentary",
    "share commentary",
    "commentary",
    "content",
    "text",
    "title",
)
DATE_COLUMNS = ("sharedate", "share date", "date", "created date", "published")


@dataclass
class ImportPayload:
    headline: str | None = None
    summary: str | None = None
    posts: list[PostRecord] = field(default_factory=list)
    profile_fields_updated: list[str] = field(default_factory=list)


def _normalize_header(name: str) -> str:
    return name.strip().lower().replace("_", " ")


def _pick_column(row: dict[str, str], candidates: tuple[str, ...]) -> str | None:
    normalized = {_normalize_header(k): v for k, v in row.items()}
    for candidate in candidates:
        value = normalized.get(candidate)
        if value and value.strip():
            return value.strip()
    return None


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d %b %Y",
    ):
        try:
            return datetime.strptime(value.strip()[:19], fmt)
        except ValueError:
            continue
    return None


def _read_csv_rows(data: bytes) -> list[dict[str, str]]:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = data.decode(encoding)
            reader = csv.DictReader(io.StringIO(text))
            return [dict(row) for row in reader if any(row.values())]
        except UnicodeDecodeError:
            continue
    return []


def _find_zip_members(zf: zipfile.ZipFile, hints: tuple[str, ...]) -> list[str]:
    matches = []
    for name in zf.namelist():
        lower = name.lower()
        if not lower.endswith(".csv"):
            continue
        if any(h in lower for h in hints):
            matches.append(name)
    return matches


def parse_linkedin_export_zip(data: bytes) -> ImportPayload:
    payload = ImportPayload()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for member in _find_zip_members(zf, PROFILE_FILE_HINTS):
            rows = _read_csv_rows(zf.read(member))
            if not rows:
                continue
            row = rows[0]
            headline = _pick_column(row, HEADLINE_COLUMNS)
            summary = _pick_column(row, SUMMARY_COLUMNS)
            if headline and not payload.headline:
                payload.headline = headline
                payload.profile_fields_updated.append("linkedin_headline")
            if summary and not payload.summary:
                payload.summary = summary
                payload.profile_fields_updated.append("about_summary")

        for member in _find_zip_members(zf, POST_FILE_HINTS):
            rows = _read_csv_rows(zf.read(member))
            for row in rows:
                content = _pick_column(row, CONTENT_COLUMNS)
                if not content or len(content) < 5:
                    continue
                posted_at = _parse_date(_pick_column(row, DATE_COLUMNS))
                media = _pick_column(row, ("mediatype", "media type", "type")) or "text"
                post_type = _map_post_type(media)
                payload.posts.append(
                    PostRecord(content=content, post_type=post_type, posted_at=posted_at)
                )

    logger.info(
        "Parsed LinkedIn export: %d posts, fields=%s",
        len(payload.posts),
        payload.profile_fields_updated,
    )
    return payload


def _map_post_type(media: str) -> PostType:
    lower = media.lower()
    if "video" in lower:
        return "video"
    if "poll" in lower:
        return "poll"
    if "document" in lower or "carousel" in lower or "image" in lower:
        return "carousel"
    return "text"


def apply_import_to_profile(
    user_id: str, profile: UserProfile | None, payload: ImportPayload
) -> UserProfile:
    profile = profile or UserProfile(user_id=user_id)
    if payload.headline:
        profile.linkedin_headline = payload.headline
    if payload.summary:
        profile.about_summary = payload.summary
    return profile
