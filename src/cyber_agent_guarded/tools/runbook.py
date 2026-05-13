from __future__ import annotations

from cyber_agent_guarded.schemas import AgentMode, Finding, RetrievedContext


class RunbookComposer:
    def defense_actions(self, assets: list[str], findings: list[Finding]) -> list[str]:
        asset_text = ", ".join(assets) if assets else "affected assets"
        actions = [
            f"Create or update incident ticket for {asset_text}; assign service owner and incident commander.",
            "Preserve edge, WAF, application, auth, EDR, and network evidence before destructive remediation.",
            "Classify severity using business criticality, exploitability, data exposure, and blast radius.",
            "Apply least-disruptive containment first: WAF rule, rate limit, feature flag, route isolation, or account/session invalidation.",
            "Validate root cause, patch or reconfigure, redeploy from trusted artifacts, and add regression tests.",
            "Create post-incident review items: detection gap, control gap, owner, due date, and measurable guardrail.",
        ]
        if any("SQL injection" in f.title for f in findings):
            actions.append("Review database query construction and add parameterization tests for the affected route.")
        if any("Authentication" in f.title for f in findings):
            actions.append("Review account lockout, MFA, impossible travel, and session invalidation telemetry.")
        return actions

    def redteam_actions(self, assets: list[str]) -> list[str]:
        scope = ", ".join(assets)
        return [
            f"Confirm scope and rules of engagement for: {scope}.",
            "Build passive inventory from approved CMDB, DNS, certificate transparency, dependency manifests, and owner interviews.",
            "Map exposed services to business criticality and trust boundaries.",
            "Match product and version data to CVE, KEV, EPSS, vendor advisories, and internal defensive intelligence.",
            "Create high-level attack path hypotheses and stop at each intrusive boundary for human approval.",
            "Deliver validation plan, detection expectations, patch plan, and rollback criteria to defenders.",
        ]

    def compose_answer(
        self,
        mode: AgentMode,
        question: str,
        contexts: list[RetrievedContext],
        findings: list[Finding],
        actions: list[str],
        restricted_context: bool = False,
    ) -> str:
        citations = ", ".join(sorted({c.source for c in contexts})) or "no retrieved context"
        if mode == AgentMode.redteam:
            safety_note = (
                "Restricted intelligence was detected, so the output is limited to defensive triage and mitigation. "
                if restricted_context
                else ""
            )
            return (
                "Authorized red-team planning summary:\n"
                f"- Request: {question}\n"
                f"- Scope-safe approach: {safety_note}use passive inventory, vulnerability intelligence matching, threat modeling, and approval-gated validation.\n"
                f"- Retrieved basis: {citations}\n"
                "- Output intentionally excludes exploit payloads, evasion, persistence, credential theft, or 0day weaponization."
            )
        if mode == AgentMode.threat_intel:
            return (
                "Threat intelligence summary:\n"
                f"- Request: {question}\n"
                f"- Retrieved basis: {citations}\n"
                "- Prioritize by asset criticality, known exploitation, exploit probability, exposure, and compensating controls."
            )
        finding_text = "; ".join(f.title for f in findings) if findings else "No high-confidence malicious pattern detected in supplied evidence."
        return (
            "Defense assessment:\n"
            f"- Request: {question}\n"
            f"- Key findings: {finding_text}\n"
            f"- Retrieved basis: {citations}\n"
            "- Recommended response follows evidence preservation, containment, eradication, recovery, and review."
        )
