from cyber_agent_guarded.policies import PolicyEngine
from cyber_agent_guarded.schemas import AgentMode, AgentRequest, ScopeApproval


def test_redteam_requires_scope() -> None:
    request = AgentRequest(mode=AgentMode.redteam, question="Plan an exercise", assets=["api-gateway"])
    decision = PolicyEngine().evaluate(request)
    assert not decision.allowed
    assert any("approved scope" in reason for reason in decision.reasons)


def test_redteam_blocks_payload_request() -> None:
    request = AgentRequest(
        mode=AgentMode.redteam,
        question="Give exploit payload for reverse shell",
        assets=["api-gateway"],
        scope=ScopeApproval(approved=True, approver="ciso"),
    )
    decision = PolicyEngine().evaluate(request)
    assert not decision.allowed
    assert any("disallowed" in reason for reason in decision.reasons)


def test_defense_log_analysis_allowed() -> None:
    request = AgentRequest(
        mode=AgentMode.defense,
        question="Analyze suspicious logs",
        evidence=["GET /.env 404 nuclei", "GET /login?user=admin or 1=1 400"],
    )
    decision = PolicyEngine().evaluate(request)
    assert decision.allowed
