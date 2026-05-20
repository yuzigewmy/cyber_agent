from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from cyber_agent_guarded.config import Settings

_bearer = HTTPBearer(auto_error=False)

REGISTERED_USERS: dict[str, str] = {}


@dataclass(frozen=True)
class AuthenticatedUser:
    """Authenticated user context attached to API requests."""

    user_id: str
    username: str
    roles: list[str]


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _sign(message: str, secret: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(digest)


def create_access_token(
    *,
    username: str,
    roles: list[str],
    settings: Settings,
    now: int | None = None,
) -> str:
    """Create a compact HMAC-signed token for the MVP.

    Production deployments should replace this module with OIDC/SSO,
    LDAP, SAML, Keycloak, API Gateway auth, or enterprise IAM.
    """

    issued_at = int(now or time.time())
    expires_at = issued_at + settings.auth.access_token_ttl_minutes * 60

    header = {
        "alg": "HS256",
        "typ": "JWT",
    }

    payload: dict[str, Any] = {
        "sub": username,
        "roles": roles,
        "iat": issued_at,
        "exp": expires_at,
    }

    signing_input = ".".join(
        [
            _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
    )

    return f"{signing_input}.{_sign(signing_input, settings.auth.secret)}"


def verify_access_token(
    token: str,
    settings: Settings,
    now: int | None = None,
) -> AuthenticatedUser:
    try:
        header_b64, payload_b64, signature = token.split(".", 2)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token format.",
        ) from exc

    signing_input = f"{header_b64}.{payload_b64}"
    expected = _sign(signing_input, settings.auth.secret)

    if not hmac.compare_digest(signature, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token signature.",
        )

    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token payload.",
        ) from exc

    if int(payload.get("exp", 0)) < int(now or time.time()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired.",
        )

    username = str(payload.get("sub") or "")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token subject missing.",
        )

    roles = payload.get("roles") or []
    if not isinstance(roles, list):
        roles = []

    return AuthenticatedUser(
        user_id=username,
        username=username,
        roles=[str(role) for role in roles],
    )


def register_user(username: str, password: str) -> AuthenticatedUser:
    """Register a simple in-memory user.

    This is only for demo usage.
    Users will be lost after service restart.
    """

    username = username.strip()

    if not username or not password:
        raise ValueError("Username and password are required.")

    if username in REGISTERED_USERS:
        raise ValueError("Username already exists.")

    REGISTERED_USERS[username] = password

    return AuthenticatedUser(
        user_id=username,
        username=username,
        roles=["SOC Analyst"],
    )


def authenticate_demo_user(
    username: str,
    password: str,
    settings: Settings,
) -> AuthenticatedUser | None:
    """Validate built-in demo user or in-memory registered users."""

    is_demo_user = (
        hmac.compare_digest(username, settings.auth.demo_username)
        and hmac.compare_digest(password, settings.auth.demo_password)
    )

    if is_demo_user:
        return AuthenticatedUser(
            user_id=username,
            username=username,
            roles=["SOC Analyst", "Incident Commander", "Red Team Lead"],
        )

    registered_password = REGISTERED_USERS.get(username)

    if registered_password is not None and hmac.compare_digest(password, registered_password):
        return AuthenticatedUser(
            user_id=username,
            username=username,
            roles=["SOC Analyst"],
        )

    return None


def get_current_user_factory(settings: Settings | None = None):
    def _get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    ) -> AuthenticatedUser:
        resolved_settings = settings
        if resolved_settings is None:
            from cyber_agent_guarded.runtime import get_settings

            resolved_settings = get_settings()

        if not resolved_settings.auth.enabled:
            return AuthenticatedUser(
                user_id="anonymous",
                username="anonymous",
                roles=["anonymous"],
            )

        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token.",
            )

        return verify_access_token(credentials.credentials, resolved_settings)

    return _get_current_user
