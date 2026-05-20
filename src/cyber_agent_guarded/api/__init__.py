from __future__ import annotations

from fastapi import APIRouter

from cyber_agent_guarded.api import auth, chat, system


def api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(system.router)
    router.include_router(auth.router)
    router.include_router(chat.router)
    return router
