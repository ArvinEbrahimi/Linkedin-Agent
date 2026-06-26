from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request

from app.config import Settings, get_settings
from app.core.exceptions import ConfigurationError
from app.services.advisor import AdvisorService
from app.services.auth import AuthError, AuthService
from app.services.auth_store import Account
from app.services.content import ContentService
from app.services.linkedin import LinkedInService
from app.services.memory_store import MemoryService
from app.services.networking import NetworkingService
from app.services.profile import ProfileService
from app.services.strategy import StrategyService


def get_graph(request: Request):
    graph = getattr(request.app.state, "graph", None)
    if graph is None:
        raise ConfigurationError("Agent graph is not initialized")
    return graph


def get_auth_service(request: Request) -> AuthService:
    service = getattr(request.app.state, "auth_service", None)
    if service is None:
        raise ConfigurationError("Auth service is not initialized")
    return service


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    return token or None


async def resolve_account(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> Account | None:
    settings: Settings = get_settings()
    token = _bearer_token(authorization)
    if not token:
        if settings.auth_required:
            raise HTTPException(status_code=401, detail="Authentication required")
        return None
    auth = get_auth_service(request)
    try:
        user_id = auth.decode_token(token)
        return auth.get_account(user_id)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=exc.message) from exc


async def require_account(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> Account:
    account = await resolve_account(request, authorization)
    if account is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return account


async def attach_account_middleware(request: Request, call_next):
    settings = get_settings()
    token = _bearer_token(request.headers.get("authorization"))
    request.state.account = None
    if token and getattr(request.app.state, "auth_service", None):
        try:
            user_id = request.app.state.auth_service.decode_token(token)
            request.state.account = request.app.state.auth_service.get_account(user_id)
        except AuthError:
            request.state.account = None
    response = await call_next(request)
    return response


def assert_user_access(account: Account | None, user_id: str, settings: Settings) -> None:
    if not settings.auth_required:
        return
    if account is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if account.id != user_id:
        raise HTTPException(status_code=403, detail="Cannot access another user's data")


def get_content_service(request: Request) -> ContentService:
    service = getattr(request.app.state, "content_service", None)
    if service is None:
        raise ConfigurationError("Content service is not initialized")
    return service


def get_networking_service(request: Request) -> NetworkingService:
    service = getattr(request.app.state, "networking_service", None)
    if service is None:
        raise ConfigurationError("Networking service is not initialized")
    return service


def get_profile_service(request: Request) -> ProfileService:
    service = getattr(request.app.state, "profile_service", None)
    if service is None:
        raise ConfigurationError("Profile service is not initialized")
    return service


def get_memory_service(request: Request) -> MemoryService:
    service = getattr(request.app.state, "memory_service", None)
    if service is None:
        raise ConfigurationError("Memory service is not initialized")
    return service


def get_advisor_service(request: Request) -> AdvisorService:
    service = getattr(request.app.state, "advisor_service", None)
    if service is None:
        raise ConfigurationError("Advisor service is not initialized")
    return service


def get_strategy_service(request: Request) -> StrategyService:
    service = getattr(request.app.state, "strategy_service", None)
    if service is None:
        raise ConfigurationError("Strategy service is not initialized")
    return service


def get_linkedin_service(request: Request) -> LinkedInService:
    service = getattr(request.app.state, "linkedin_service", None)
    if service is None:
        raise ConfigurationError("LinkedIn service is not initialized")
    return service
