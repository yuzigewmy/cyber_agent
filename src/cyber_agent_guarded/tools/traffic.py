from __future__ import annotations

import re
from collections import Counter

from cyber_agent_guarded.schemas import Finding


class TrafficAnalyzer:
    """Rule-based triage for HTTP and proxy log snippets.

    This module is intentionally conservative and explainable. Feed full logs to
    a SIEM query layer in production and pass only relevant excerpts here.
    """

    SQLI = re.compile(r"('|%27|\bor\b\s+1=1|union\s+select|sleep\s*\(|benchmark\s*\()", re.I)
    TRAVERSAL = re.compile(r"(\.\./|%2e%2e%2f|/etc/passwd|boot\.ini)", re.I)
    SECRET_PATH = re.compile(r"(/\.env|/config\.json|/wp-config\.php|/actuator/env)", re.I)
    SCANNER_UA = re.compile(r"(sqlmap|nuclei|masscan|zgrab|nikto|acunetix|nessus)", re.I)
    AUTH_BURST = re.compile(r"(401|403).*(login|auth|session|token)", re.I)

    def analyze(self, evidence: list[str]) -> list[Finding]:
        findings: list[Finding] = []
        joined = "\n".join(evidence)

        if self.SQLI.search(joined):
            findings.append(
                Finding(
                    title="Possible SQL injection probing",
                    severity="high",
                    evidence=[line for line in evidence if self.SQLI.search(line)][:5],
                    mapping=["ATT&CK T1190 Exploit Public-Facing Application"],
                    recommendation="Add or tune WAF signatures, verify parameterized queries, and review application errors and database logs.",
                )
            )
        if self.TRAVERSAL.search(joined):
            findings.append(
                Finding(
                    title="Possible path traversal probing",
                    severity="high",
                    evidence=[line for line in evidence if self.TRAVERSAL.search(line)][:5],
                    mapping=["ATT&CK T1190 Exploit Public-Facing Application"],
                    recommendation="Block traversal patterns, verify file access controls, and check whether sensitive files were returned.",
                )
            )
        if self.SECRET_PATH.search(joined):
            findings.append(
                Finding(
                    title="Sensitive path discovery attempt",
                    severity="medium",
                    evidence=[line for line in evidence if self.SECRET_PATH.search(line)][:5],
                    mapping=["ATT&CK T1595 Active Scanning"],
                    recommendation="Confirm HTTP response codes and rotate secrets if any sensitive file was exposed.",
                )
            )
        if self.SCANNER_UA.search(joined):
            findings.append(
                Finding(
                    title="Known scanner signature observed",
                    severity="medium",
                    evidence=[line for line in evidence if self.SCANNER_UA.search(line)][:5],
                    mapping=["ATT&CK T1595 Active Scanning"],
                    recommendation="Rate-limit source networks, tag IOCs, and correlate with edge firewall and WAF events.",
                )
            )
        auth_count = sum(1 for line in evidence if self.AUTH_BURST.search(line))
        if auth_count >= 3:
            findings.append(
                Finding(
                    title="Authentication failure burst",
                    severity="medium",
                    evidence=[line for line in evidence if self.AUTH_BURST.search(line)][:5],
                    mapping=["ATT&CK T1110 Brute Force"],
                    recommendation="Enable adaptive throttling, review source IP reputation, and verify MFA/session anomalies.",
                )
            )

        source_counter = Counter()
        ip_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
        for line in evidence:
            match = ip_pattern.search(line)
            if match:
                source_counter[match.group(0)] += 1
        noisy_sources = [ip for ip, count in source_counter.items() if count >= 5]
        if noisy_sources:
            findings.append(
                Finding(
                    title="High-volume source observed",
                    severity="low",
                    evidence=noisy_sources[:10],
                    mapping=["ATT&CK T1595 Active Scanning"],
                    recommendation="Review rate, geo, ASN, and whether requests hit sensitive endpoints before blocking.",
                )
            )
        return findings


def highest_severity(findings: list[Finding]) -> str:
    order = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    if not findings:
        return "info"
    return max((f.severity for f in findings), key=lambda x: order.get(x, 0))
