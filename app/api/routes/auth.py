"""Authentication API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field

from app.api.deps import get_auth_service, require_account
from app.core.exceptions import LinkAidError
from app.services.auth import AuthError, AuthService
from app.services.auth_store import Account

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    display_name: str


class MeResponse(BaseModel):
    user_id: str
    email: str
    display_name: str


def _auth_response(account, token: str) -> AuthResponse:
    return AuthResponse(
        access_token=token,
        user_id=account.id,
        email=account.email,
        display_name=account.display_name,
    )


@router.post("/register", response_model=AuthResponse, summary="Create account")
async def register(
    body: RegisterRequest,
    auth: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        account, token = auth.register(body.email, body.password, body.display_name)
    except AuthError:
        raise
    except LinkAidError:
        raise
    return _auth_response(account, token)


@router.post("/login", response_model=AuthResponse, summary="Login")
async def login(
    body: LoginRequest,
    auth: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    account, token = auth.login(body.email, body.password)
    return _auth_response(account, token)


@router.get("/me", response_model=MeResponse, summary="Current account")
async def me(account: Account = Depends(require_account)) -> MeResponse:
    return MeResponse(
        user_id=account.id,
        email=account.email,
        display_name=account.display_name,
    )
