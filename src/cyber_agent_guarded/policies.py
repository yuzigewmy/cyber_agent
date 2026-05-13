from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from cyber_agent_guarded.schemas import AgentMode, AgentRequest, RetrievedContext


@dataclass
class SafetyDecision:
    allowed: bool
    reasons: list[str] = field(default_factory=list)
    requires_human_approval: bool = False
    restricted_context: bool = False


class PolicyEngine:
    """A conservative policy layer for dual-use security workflows.

    The rules are intentionally simple and auditable. In production, pair this
    with classifier models, allowlists, tenant RBAC, and manual review queues.
    """

    def __init__(self, require_scope_for_redteam: bool = True) -> None:
        self.require_scope_for_redteam = require_scope_for_redteam
        self.hard_block_patterns = [
            r"\bexploit\s+(code|chain|payload|script)\b",
            r"\bweaponiz(e|ation|ed)\b",
            r"\bshellcode\b",
            r"\breverse\s+shell\b",
            r"\bwebshell\b",
            r"\bcredential\s+(dump|theft|steal|harvest)\b",
            r"\bpassword\s+(dump|spray|crack|steal)\b",
            r"\bphish(ing)?\b",
            r"\bmalware\b",
            r"\bransomware\b",
            r"\bkeylogger\b",
            r"\bbypass\s+(edr|av|waf|mfa|detection)\b",
            r"\bevade\s+(edr|av|detection|logging)\b",
            r"\bpersistence\b",
            r"\bexfiltrat(e|ion)\b",
            r"\bdropper\b",
            r"\bc2\s+(server|implant|beacon)\b",
            r"\b0day\s+(exploit|payload|poc)\b",
            r"\bzero[- ]day\s+(exploit|payload|poc)\b",
            # Chinese terms encoded as escapes to keep source ASCII-only.
            "\u53cd\u5f39\\s*shell",
            "\u6728\u9a6c",
            "\u52d2\u7d22\u8f6f\u4ef6",
            "\u514d\u6740",
            "\u7ed5\u8fc7\\s*(edr|av|waf|mfa|\u68c0\u6d4b)",
            "\u51ed\u636e\\s*(\u7a83\u53d6|\u6293\u53d6|\u76d7\u53d6)",
            "\u6570\u636e\\s*\u5916\u4f20",
            "\u6b66\u5668\u5316",
        ]

    def evaluate(
        self,
        request: AgentRequest,
        retrieved_contexts: Iterable[RetrievedContext] | None = None,
    ) -> SafetyDecision:
        text = " ".join([request.question, *request.assets, *request.evidence]).lower()
        reasons: list[str] = []

        for pattern in self.hard_block_patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                reasons.append(f"Request matches disallowed operational pattern: {pattern}")

        requires_approval = False
        if request.mode == AgentMode.redteam:
            if self.require_scope_for_redteam and not request.scope.approved:
                reasons.append("Authorized red-team mode requires an approved scope.")
            if not request.assets:
                reasons.append("Authorized red-team mode requires explicit in-scope assets.")
            requires_approval = True

        restricted_context = False
        for ctx in retrieved_contexts or []:
            sensitivity = (ctx.sensitivity or "").lower()
            if "0day" in sensitivity or "restricted" in sensitivity:
                restricted_context = True
                if request.mode == AgentMode.redteam:
                    reasons.append(
                        "Restricted vulnerability intelligence may only be summarized for defensive triage and mitigation."
                    )

        return SafetyDecision(
            allowed=len(reasons) == 0,
            reasons=reasons,
            requires_human_approval=requires_approval,
            restricted_context=restricted_context,
        )
