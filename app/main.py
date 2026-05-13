from __future__ import annotations

from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from cyber_agent_guarded.agent import CyberAgent
from cyber_agent_guarded.auth import (
    AuthenticatedUser,
    authenticate_demo_user,
    create_access_token,
    get_current_user_factory,
    register_user,
)
from cyber_agent_guarded.config import load_settings
from cyber_agent_guarded.schemas import (
    AgentRequest,
    AgentResponse,
    ChatMessageRecord,
    ChatSessionCreate,
    ChatSessionSummary,
    LoginRequest,
    LoginResponse,
    UserProfile,
)
from cyber_agent_guarded.storage.chat_repository import (
    create_session,
    list_messages,
    list_sessions,
    persist_chat_turn,
    serialize_message,
    serialize_session,
)
from cyber_agent_guarded.storage.database import get_db, init_db

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path(
    os.getenv(
        "CYBER_AGENT_CONFIG_PATH",
        BASE_DIR / "config" / "config.example.yaml",
    )
)

settings = load_settings(CONFIG_PATH)
agent = CyberAgent(settings=settings, base_dir=str(BASE_DIR))
get_current_user = get_current_user_factory(settings)

app = FastAPI(
    title="Cyber Agent Guarded API",
    version="0.3.0",
)

allowed_origins = os.getenv(
    "CYBER_AGENT_CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
).split(",")

init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": settings.agent.name,
        "service": "Cyber Agent Guarded API",
        "frontend": "Run the separated Vue app in frontend-vue/.",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "agent": settings.agent.name,
    }


@app.post("/v1/auth/register", response_model=UserProfile)
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


@app.post("/v1/auth/login", response_model=LoginResponse)
def login(request: LoginRequest) -> LoginResponse:
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


@app.get("/v1/auth/me", response_model=UserProfile)
def me(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UserProfile:
    return UserProfile(
        username=current_user.username,
        roles=current_user.roles,
    )


@app.post("/v1/chat", response_model=AgentResponse)
def chat(
    request: AgentRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AgentResponse:
    request_with_user = request.model_copy(
        update={
            "user_id": current_user.user_id,
        }
    )

    response = agent.handle(request_with_user)

    persist_chat_turn(
        db,
        user_id=current_user.user_id,
        request=request_with_user,
        response=response,
    )

    return response


@app.post("/v1/chat/sessions", response_model=ChatSessionSummary)
def create_chat_session(
    request: ChatSessionCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    session = create_session(
        db,
        user_id=current_user.user_id,
        tenant_id=request.tenant_id,
        mode=request.mode.value,
        title=request.title,
    )

    return serialize_session(session)


@app.get("/v1/chat/sessions", response_model=list[ChatSessionSummary])
def get_chat_sessions(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    return [
        serialize_session(session)
        for session in list_sessions(
            db,
            user_id=current_user.user_id,
        )
    ]


@app.get(
    "/v1/chat/sessions/{session_id}/messages",
    response_model=list[ChatMessageRecord],
)
def get_chat_messages(
    session_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    return [
        serialize_message(message)
        for message in list_messages(
            db,
            session_id=session_id,
            user_id=current_user.user_id,
        )
    ]