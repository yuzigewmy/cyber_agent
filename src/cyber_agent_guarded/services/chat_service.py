from __future__ import annotations

from sqlalchemy.orm import Session

from cyber_agent_guarded.agent import CyberAgent
from cyber_agent_guarded.auth import AuthenticatedUser
from cyber_agent_guarded.schemas import AgentRequest, AgentResponse
from cyber_agent_guarded.storage.chat_repository import persist_chat_turn


class ChatService:
    """Coordinates agent execution and chat persistence."""

    def __init__(self, agent: CyberAgent) -> None:
        self.agent = agent

    def handle_turn(
        self,
        *,
        db: Session,
        current_user: AuthenticatedUser,
        request: AgentRequest,
    ) -> AgentResponse:
        request_with_user = request.model_copy(
            update={
                "user_id": current_user.user_id,
            }
        )

        response = self.agent.handle(request_with_user)

        persist_chat_turn(
            db,
            user_id=current_user.user_id,
            request=request_with_user,
            response=response,
        )

        return response
