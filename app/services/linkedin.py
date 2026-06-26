"""LinkedIn connect + data import orchestration."""

from __future__ import annotations

import logging

from app.config import Settings
from app.models.linkedin import LinkedInImportResult
from app.services.linkedin_import import (
    apply_import_to_profile,
    parse_linkedin_export_zip,
)
from app.services.linkedin_oauth import LinkedInOAuthService
from app.services.memory_store import MemoryService

logger = logging.getLogger(__name__)

MAX_IMPORT_POSTS = 100


class LinkedInService:
    def __init__(self, settings: Settings, memory_service: MemoryService) -> None:
        self.settings = settings
        self.memory = memory_service
        self.oauth = LinkedInOAuthService(settings, memory_service)

    def import_data_export(self, user_id: str, file_bytes: bytes) -> LinkedInImportResult:
        if not file_bytes:
            raise ValueError("Empty file uploaded")

        payload = parse_linkedin_export_zip(file_bytes)
        profile = apply_import_to_profile(user_id, self.memory.get_profile(user_id), payload)
        self.memory.save_profile(user_id, profile)

        imported = 0
        for post in payload.posts[:MAX_IMPORT_POSTS]:
            self.memory.add_post(user_id, post)
            imported += 1

        message = (
            f"Imported {imported} posts"
            + (
                f" and updated {', '.join(payload.profile_fields_updated)}"
                if payload.profile_fields_updated
                else ""
            )
            + "."
        )
        return LinkedInImportResult(
            user_id=user_id,
            posts_imported=imported,
            profile_fields_updated=payload.profile_fields_updated,
            headline=payload.headline,
            summary=payload.summary,
            message=message,
        )
