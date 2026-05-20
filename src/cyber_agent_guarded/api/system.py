from __future__ import annotations

from fastapi import APIRouter

from cyber_agent_guarded.api.dependencies import AgentDep, SettingsDep
from cyber_agent_guarded.schemas import AgentMode

router = APIRouter(tags=["system"])


@router.get("/")
def root(settings: SettingsDep) -> dict[str, str]:
    return {
        "name": settings.agent.name,
        "service": "Cyber Agent Guarded API",
        "frontend": "Run the separated Vue app in frontend-vue/.",
    }


@router.get("/health")
def health(settings: SettingsDep) -> dict[str, str]:
    return {
        "status": "ok",
        "agent": settings.agent.name,
    }


@router.get("/v1/system/capabilities")
def capabilities(settings: SettingsDep, agent: AgentDep) -> dict[str, object]:
    return {
        "agent": settings.agent.name,
        "modes": [mode.value for mode in AgentMode],
        "rag_backend": settings.rag.backend,
        "max_retrieved_docs": settings.agent.max_retrieved_docs,
        "tools": agent.tools.capabilities(),
        "llm_available": agent.llm.available,
        "graph_enabled": agent.graph is not None,
        "safety": {
            "require_scope_for_redteam": settings.agent.require_scope_for_redteam,
            "redteam_output_level": settings.safety.redteam_output_level,
            "allow_exploit_code": settings.safety.allow_exploit_code,
            "allow_payload_generation": settings.safety.allow_payload_generation,
            "allow_credential_theft": settings.safety.allow_credential_theft,
            "allow_evasion_or_persistence": settings.safety.allow_evasion_or_persistence,
        },
    }
