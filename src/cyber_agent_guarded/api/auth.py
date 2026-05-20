from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from cyber_agent_guarded.api.dependencies import SettingsDep
from cyber_agent_guarded.auth import (
    AuthenticatedUser,
    authenticate_demo_user,
    create_access_token,
    get_current_user_factory,
    register_user,
)
from cyber_agent_guarded.schemas import LoginRequest, LoginResponse, UserProfile

router = APIRouter(prefix="/v1/auth", tags=["auth"])
CurrentUserDep = Annotated[AuthenticatedUser, Depends(get_current_user_factory())]


@router.post("/register", response_model=UserProfile)
def register(request: LoginRequest) -> UserProfile:
    try:
        user = register_user(request.username, request.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return UserProfile(
        username=user.username,
        roles=user.roles,
    )


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, settings: SettingsDep) -> LoginResponse:
    user = authenticate_demo_user(request.username, request.password, settings)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    token = create_access_token(
        username=user.username,
        roles=user.roles,
        settings=settings,
    )

    return LoginResponse(
        access_token=token,
        expires_in=settings.auth.access_token_ttl_minutes * 60,
        username=user.username,
        roles=user.roles,
    )


@router.get("/me", response_model=UserProfile)
def me(user: CurrentUserDep) -> UserProfile:
    return UserProfile(
        username=user.username,
        roles=user.roles,
    )
