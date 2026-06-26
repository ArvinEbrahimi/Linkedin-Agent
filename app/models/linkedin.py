from datetime import datetime

from pydantic import BaseModel, Field


class LinkedInUserInfo(BaseModel):
    sub: str
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    email: str | None = None
    picture: str | None = None
    locale: str | None = None


class LinkedInAuthUrlResponse(BaseModel):
    auth_url: str
    state: str


class LinkedInStatusResponse(BaseModel):
    user_id: str
    connected: bool
    linkedin_sub: str | None = None
    name: str | None = None
    email: str | None = None
    picture: str | None = None
    connected_at: datetime | None = None
    import_available: bool = True


class LinkedInImportResult(BaseModel):
    user_id: str
    posts_imported: int = 0
    profile_fields_updated: list[str] = Field(default_factory=list)
    headline: str | None = None
    summary: str | None = None
    message: str
