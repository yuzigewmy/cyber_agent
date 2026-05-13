from pathlib import Path

from cyber_agent_guarded.agent import CyberAgent
from cyber_agent_guarded.schemas import AgentMode, AgentRequest, ScopeApproval

BASE = Path(__file__).resolve().parents[1]


def test_agent_defense_response() -> None:
    agent = CyberAgent(base_dir=str(BASE))
    response = agent.handle(
        AgentRequest(
            mode=AgentMode.defense,
            question="Analyze logs",
            assets=["api-gateway"],
            evidence=["GET /login?user=admin or 1=1", "GET /.env 404 nuclei"],
        )
    )
    assert not response.blocked
    assert response.findings
    assert response.actions


def test_agent_redteam_safe_plan() -> None:
    agent = CyberAgent(base_dir=str(BASE))
    response = agent.handle(
        AgentRequest(
            mode=AgentMode.redteam,
            question="Create a safe red-team exercise plan",
            assets=["api-gateway"],
            scope=ScopeApproval(approved=True, approver="ciso"),
        )
    )
    assert not response.blocked
    assert response.requires_human_approval
    assert "exploit payloads" in response.answer
