from __future__ import annotations

from fastapi import APIRouter

from cyber_agent_guarded.api.auth import CurrentUserDep
from cyber_agent_guarded.api.dependencies import AgentDep, DbDep
from cyber_agent_guarded.schemas import (
    AgentRequest,
    AgentResponse,
    ChatMessageRecord,
    ChatSessionCreate,
    ChatSessionSummary,
)
from cyber_agent_guarded.services.chat_service import ChatService
from cyber_agent_guarded.storage.chat_repository import (
    create_session,
    list_messages,
    list_sessions,
    serialize_message,
    serialize_session,
)

router = APIRouter(prefix="/v1/chat", tags=["chat"])


@router.post("", response_model=AgentResponse)
def chat(
    request: AgentRequest,
    agent: AgentDep,
    db: DbDep,
    user: CurrentUserDep,
) -> AgentResponse:
    return ChatService(agent).handle_turn(
        db=db,
        current_user=user,
        request=request,
    )


@router.post("/sessions", response_model=ChatSessionSummary)
def create_chat_session(
    request: ChatSessionCreate,
    db: DbDep,
    user: CurrentUserDep,
) -> dict[str, object]:
    session = create_session(
        db,
        user_id=user.user_id,
        tenant_id=request.tenant_id,
        mode=request.mode.value,
        title=request.title,
    )

    return serialize_session(session)


@router.get("/sessions", response_model=list[ChatSessionSummary])
def get_chat_sessions(
    db: DbDep,
    user: CurrentUserDep,
) -> list[dict[str, object]]:
    return [
        serialize_session(session)
        for session in list_sessions(
            db,
            user_id=user.user_id,
        )
    ]


@router.get(
    "/sessions/{session_id}/messages",
    response_model=list[ChatMessageRecord],
)
def get_chat_messages(
    session_id: str,
    db: DbDep,
    user: CurrentUserDep,
) -> list[dict[str, object]]:
    return [
        serialize_message(message)
        for message in list_messages(
            db,
            session_id=session_id,
            user_id=user.user_id,
        )
    ]
