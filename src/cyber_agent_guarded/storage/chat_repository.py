from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from cyber_agent_guarded.schemas import AgentRequest, AgentResponse
from cyber_agent_guarded.storage.models import ChatMessage, ChatSession, utcnow


def _title_from_question(question: str) -> str:
    clean = " ".join(question.strip().split())
    if not clean:
        return "New conversation"
    return clean[:70] + ("..." if len(clean) > 70 else "")


def create_session(
    db: Session,
    *,
    user_id: str,
    tenant_id: str,
    mode: str,
    title: str | None = None,
) -> ChatSession:
    session = ChatSession(
        user_id=user_id,
        tenant_id=tenant_id,
        mode=mode,
        title=title or "New conversation",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_user_session(db: Session, *, session_id: str, user_id: str) -> ChatSession | None:
    return db.scalar(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    )


def list_sessions(db: Session, *, user_id: str, limit: int = 50) -> list[ChatSession]:
    return list(
        db.scalars(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(desc(ChatSession.updated_at))
            .limit(limit)
        )
    )


def list_messages(db: Session, *, session_id: str, user_id: str) -> list[ChatMessage]:
    session = get_user_session(db, session_id=session_id, user_id=user_id)
    if session is None:
        return []
    return list(
        db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        )
    )


def add_message(
    db: Session,
    *,
    session_id: str,
    user_id: str,
    role: str,
    mode: str,
    content: str,
    payload: dict[str, Any] | None = None,
) -> ChatMessage:
    message = ChatMessage(
        session_id=session_id,
        user_id=user_id,
        role=role,
        mode=mode,
        content=content,
        payload=payload or {},
    )
    db.add(message)
    session = db.get(ChatSession, session_id)
    if session is not None:
        session.updated_at = utcnow()
        if session.title == "New conversation" and role == "user":
            session.title = _title_from_question(content)
            session.mode = mode
    db.commit()
    db.refresh(message)
    return message


def persist_chat_turn(
    db: Session,
    *,
    user_id: str,
    request: AgentRequest,
    response: AgentResponse,
) -> tuple[ChatSession, ChatMessage, ChatMessage]:
    session: ChatSession | None = None
    if request.session_id:
        session = get_user_session(db, session_id=request.session_id, user_id=user_id)
    if session is None:
        session = create_session(
            db,
            user_id=user_id,
            tenant_id=request.tenant_id,
            mode=request.mode.value if hasattr(request.mode, "value") else str(request.mode),
            title=_title_from_question(request.question),
        )

    user_message = add_message(
        db,
        session_id=session.id,
        user_id=user_id,
        role="user",
        mode=request.mode.value if hasattr(request.mode, "value") else str(request.mode),
        content=request.question,
        payload={
            "assets": request.assets,
            "evidence": request.evidence,
            "scope": request.scope.model_dump(),
            "metadata": request.metadata,
        },
    )
    assistant_message = add_message(
        db,
        session_id=session.id,
        user_id=user_id,
        role="assistant",
        mode=response.mode.value if hasattr(response.mode, "value") else str(response.mode),
        content=response.answer,
        payload=response.model_dump(mode="json"),
    )
    response.session_id = session.id
    return session, user_message, assistant_message


def serialize_session(session: ChatSession) -> dict[str, Any]:
    return {
        "id": session.id,
        "title": session.title,
        "mode": session.mode,
        "tenant_id": session.tenant_id,
        "created_at": _iso(session.created_at),
        "updated_at": _iso(session.updated_at),
    }


def serialize_message(message: ChatMessage) -> dict[str, Any]:
    return {
        "id": message.id,
        "session_id": message.session_id,
        "role": message.role,
        "mode": message.mode,
        "content": message.content,
        "payload": message.payload or {},
        "created_at": _iso(message.created_at),
    }


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        return value.isoformat() + "Z"
    return value.isoformat()
