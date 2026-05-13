from __future__ import annotations

import json
from typing import Any, Literal, TypedDict, cast

from cyber_agent_guarded.config import Settings, load_settings
from cyber_agent_guarded.llm import LLMClient
from cyber_agent_guarded.policies import PolicyEngine, SafetyDecision
from cyber_agent_guarded.rag.ingest import build_in_memory_kb
from cyber_agent_guarded.schemas import (
    AgentMode,
    AgentRequest,
    AgentResponse,
    Finding,
    RetrievedContext,
)
from cyber_agent_guarded.tools.attack_mapping import AttackPathModeler
from cyber_agent_guarded.tools.runbook import RunbookComposer
from cyber_agent_guarded.tools.traffic import TrafficAnalyzer, highest_severity

RouteName = Literal["blocked", "defense", "threat_intel", "redteam"]


class GraphState(TypedDict, total=False):
    request: AgentRequest
    response: AgentResponse
    query: str
    filters: dict[str, object]
    route: RouteName
    contexts: list[RetrievedContext]
    findings: list[Finding]
    actions: list[str]
    decision: SafetyDecision
    severity: str
    answer: str
    model_answer: str
    llm_provider: str
    llm_error: str | None
    policy_reasons: list[str]


class CyberAgent:
    """Cyber security intelligence agent with 8 LangGraph business nodes.

    Business nodes:
      1. classify_intent
      2. retrieve_contexts
      3. policy_gate
      4. defense_analyzer
      5. threat_intel_analyzer
      6. redteam_planner
      7. runbook_composer
      8. response_composer

    The external API remains:
      agent.handle(request)
    """

    def __init__(self, settings: Settings | None = None, base_dir: str = ".") -> None:
        self.settings = settings or load_settings()
        self.kb = build_in_memory_kb(self.settings.rag, base_dir=base_dir)
        self.policy = PolicyEngine(
            require_scope_for_redteam=self.settings.agent.require_scope_for_redteam
        )
        self.traffic = TrafficAnalyzer()
        self.runbook = RunbookComposer()
        self.attack_modeler = AttackPathModeler()
        self.llm = LLMClient()
        self.graph: Any | None = None

        try:
            self.graph = build_langgraph(self)
        except RuntimeError:
            self.graph = None

    def handle(self, request: AgentRequest) -> AgentResponse:
        if self.graph is not None:
            state = self.graph.invoke({"request": request})
            response = state.get("response")
            if isinstance(response, AgentResponse):
                return response

        state = self._handle_linear({"request": request})
        return state["response"]

    def _handle_linear(self, state: GraphState) -> GraphState:
        state = self._node_classify_intent(state)
        state = self._node_retrieve_contexts(state)
        state = self._node_policy_gate(state)

        route = self._route_after_policy(state)

        if route == "defense":
            state = self._node_defense_analyzer(state)
            state = self._node_runbook_composer(state)
        elif route == "threat_intel":
            state = self._node_threat_intel_analyzer(state)
            state = self._node_runbook_composer(state)
        elif route == "redteam":
            state = self._node_redteam_planner(state)
            state = self._node_runbook_composer(state)

        state = self._node_response_composer(state)
        return state

    def _node_classify_intent(self, state: GraphState) -> GraphState:
        request = state["request"]

        query = " ".join(
            [
                request.question,
                *request.assets,
                *request.evidence,
            ]
        )

        filters = self._filters_for_mode(request.mode)

        if request.mode == AgentMode.redteam:
            route: RouteName = "redteam"
        elif request.mode == AgentMode.threat_intel:
            route = "threat_intel"
        else:
            route = "defense"

        return {
            **state,
            "query": query,
            "filters": filters,
            "route": route,
            "findings": state.get("findings", []),
            "actions": state.get("actions", []),
        }

    def _node_retrieve_contexts(self, state: GraphState) -> GraphState:
        query = state.get("query", "")
        filters = state.get("filters", {})

        contexts = self.kb.search(
            query,
            k=self.settings.agent.max_retrieved_docs,
            filters=filters if filters else None,
        )

        return {
            **state,
            "contexts": contexts,
        }

    def _node_policy_gate(self, state: GraphState) -> GraphState:
        request = state["request"]
        contexts = state.get("contexts", [])

        decision = self.policy.evaluate(request, contexts)

        return {
            **state,
            "decision": decision,
            "policy_reasons": decision.reasons,
        }

    def _node_defense_analyzer(self, state: GraphState) -> GraphState:
        request = state["request"]

        findings = self.traffic.analyze(request.evidence)
        severity = highest_severity(findings) if findings else "info"

        return {
            **state,
            "findings": findings,
            "severity": severity,
        }

    def _node_threat_intel_analyzer(self, state: GraphState) -> GraphState:
        request = state["request"]
        contexts = state.get("contexts", [])
        findings: list[Finding] = []

        if request.assets:
            findings.append(
                Finding(
                    title="Asset and version intelligence prioritization required",
                    severity="info",
                    evidence=request.assets[:10],
                    mapping=[
                        "CVE",
                        "CISA KEV",
                        "EPSS",
                        "Vendor Advisory",
                    ],
                    recommendation=(
                        "Enrich each asset with product, version, exposure, owner, "
                        "business criticality, KEV status, EPSS percentile, and "
                        "compensating controls."
                    ),
                )
            )
        elif contexts:
            findings.append(
                Finding(
                    title="Retrieved threat intelligence context requires owner review",
                    severity="info",
                    evidence=[context.source for context in contexts[:5]],
                    mapping=[
                        "Threat Intelligence",
                        "Vulnerability Management",
                    ],
                    recommendation=(
                        "Validate whether retrieved intelligence applies to deployed "
                        "versions before creating remediation tasks."
                    ),
                )
            )

        return {
            **state,
            "findings": findings,
            "severity": highest_severity(findings) if findings else "info",
        }

    def _node_redteam_planner(self, state: GraphState) -> GraphState:
        request = state["request"]

        path_nodes = self.attack_modeler.model(
            request.assets,
            request.evidence,
        )

        findings = [
            Finding(
                title=f"High-level exposure hypothesis for {node.asset}",
                severity="info",
                evidence=[
                    node.exposure,
                    node.validation_boundary,
                ],
                mapping=node.likely_tactics,
                recommendation=(
                    "Validate only through approved, logged, and reversible test steps."
                ),
            )
            for node in path_nodes
        ]

        return {
            **state,
            "findings": findings,
            "severity": highest_severity(findings) if findings else "info",
        }

    def _node_runbook_composer(self, state: GraphState) -> GraphState:
        request = state["request"]
        findings = state.get("findings", [])

        if request.mode == AgentMode.defense:
            actions = self.runbook.defense_actions(
                request.assets,
                findings,
            )
        elif request.mode == AgentMode.redteam:
            actions = self.runbook.redteam_actions(request.assets)
        else:
            actions = [
                "Collect product, version, exposure, owner, and business criticality.",
                "Enrich with CVE, KEV, EPSS, vendor advisory, and internal compensating controls.",
                "Prioritize remediation by known exploitation, external exposure, and critical business impact.",
            ]

        return {
            **state,
            "actions": actions,
        }

    def _node_response_composer(self, state: GraphState) -> GraphState:
        request = state["request"]
        contexts = state.get("contexts", [])
        decision = state.get("decision")

        if decision is not None and not decision.allowed:
            response = AgentResponse(
                session_id=request.session_id,
                mode=request.mode,
                blocked=True,
                severity="info",
                answer=(
                    "当前请求被安全策略拦截：请求缺少必要授权范围，或包含可能直接用于攻击执行的操作细节。"
                    "系统可以继续提供防守研判、风险分析、修复建议、检测方案和审批化演练规划。"
                ),
                citations=[context.source for context in contexts],
                retrieved_contexts=contexts,
                policy_reasons=decision.reasons,
                requires_human_approval=decision.requires_human_approval,
            )
            return {
                **state,
                "response": response,
            }

        findings = state.get("findings", [])
        actions = state.get("actions", [])
        restricted_context = bool(decision.restricted_context) if decision else False

        deterministic_answer = self.runbook.compose_answer(
            request.mode,
            request.question,
            contexts,
            findings,
            actions,
            restricted_context=restricted_context,
        )

        llm_result = self._synthesize_with_llm(
            request=request,
            contexts=contexts,
            findings=findings,
            actions=actions,
            deterministic_answer=deterministic_answer,
            restricted_context=restricted_context,
        )

        if llm_result.provider == "openai" and llm_result.content:
            answer = llm_result.content
        else:
            answer = (
                deterministic_answer
                + "\n\n"
                + "模型状态：未成功调用大模型，当前为本地规则引擎输出。"
            )
            if llm_result.error:
                answer += f"\n\n错误信息：{llm_result.error}"

        severity = cast(
            Any,
            highest_severity(findings) if findings else "info",
        )

        response = AgentResponse(
            session_id=request.session_id,
            mode=request.mode,
            blocked=False,
            severity=severity,
            answer=answer,
            findings=findings,
            actions=actions,
            citations=[context.source for context in contexts],
            retrieved_contexts=contexts,
            requires_human_approval=(
                decision.requires_human_approval if decision is not None else False
            ),
        )

        return {
            **state,
            "answer": answer,
            "severity": severity,
            "model_answer": llm_result.content,
            "llm_provider": llm_result.provider,
            "llm_error": llm_result.error,
            "response": response,
        }

    def _synthesize_with_llm(
        self,
        *,
        request: AgentRequest,
        contexts: list[RetrievedContext],
        findings: list[Finding],
        actions: list[str],
        deterministic_answer: str,
        restricted_context: bool,
    ):
        system_prompt = """
你是企业级网络安全攻防演练智库 Agent。

你的任务：
1. 基于用户问题、内部知识库上下文、工具分析结果，输出清晰、专业、可落地的安全分析。
2. 防守模式下，重点输出攻击流量研判、影响分析、应急响应、处置动作和修复建议。
3. 威胁情报模式下，重点输出漏洞优先级、资产影响、修复 SLA 和检测建议。
4. 授权红队模式下，只输出高层路径建模、验证计划、审批点和蓝队检测建议。

安全边界：
- 不输出 exploit payload。
- 不输出武器化 0day 利用步骤。
- 不输出凭据窃取、免杀、持久化、横向移动实操细节。
- 不输出绕过 EDR/WAF/MFA/检测的操作步骤。
- 如涉及高风险内容，只给防守、检测、修复、审批化验证建议。

输出风格：
- 使用中文。
- 分层清晰。
- 结论先行。
- 给出可执行但安全的防守或演练管理动作。
- 保留引用来源名称。
"""

        context_payload = [
            {
                "source": context.source,
                "collection": context.collection,
                "sensitivity": context.sensitivity,
                "score": context.score,
                "text": context.text[:1500],
            }
            for context in contexts
        ]

        finding_payload = [
            finding.model_dump(mode="json")
            for finding in findings
        ]

        user_payload = {
            "mode": request.mode.value,
            "question": request.question,
            "assets": request.assets,
            "evidence": request.evidence,
            "scope": request.scope.model_dump(mode="json"),
            "retrieved_contexts": context_payload,
            "tool_findings": finding_payload,
            "recommended_actions": actions,
            "deterministic_answer": deterministic_answer,
            "restricted_context": restricted_context,
        }

        user_prompt = (
            "请基于以下 JSON 输入，生成最终给安全运营人员看的回答：\n\n"
            + json.dumps(user_payload, ensure_ascii=False, indent=2)
        )

        return self.llm.invoke(system_prompt, user_prompt)

    def _route_after_policy(self, state: GraphState) -> RouteName:
        decision = state.get("decision")

        if decision is not None and not decision.allowed:
            return "blocked"

        return state.get("route", "defense")

    @staticmethod
    def _filters_for_mode(mode: AgentMode) -> dict[str, object]:
        if mode == AgentMode.defense:
            return {
                "collection__in": [
                    "architecture",
                    "defense",
                ]
            }

        if mode == AgentMode.redteam:
            return {
                "collection__in": [
                    "architecture",
                    "redteam",
                ]
            }

        return {}


def build_langgraph(agent: CyberAgent):
    try:
        from langgraph.graph import END, START, StateGraph  # type: ignore
    except Exception as exc:
        raise RuntimeError("Install langgraph to build the graph") from exc

    builder = StateGraph(GraphState)

    builder.add_node("classify_intent", agent._node_classify_intent)
    builder.add_node("retrieve_contexts", agent._node_retrieve_contexts)
    builder.add_node("policy_gate", agent._node_policy_gate)
    builder.add_node("defense_analyzer", agent._node_defense_analyzer)
    builder.add_node("threat_intel_analyzer", agent._node_threat_intel_analyzer)
    builder.add_node("redteam_planner", agent._node_redteam_planner)
    builder.add_node("runbook_composer", agent._node_runbook_composer)
    builder.add_node("response_composer", agent._node_response_composer)

    builder.add_edge(START, "classify_intent")
    builder.add_edge("classify_intent", "retrieve_contexts")
    builder.add_edge("retrieve_contexts", "policy_gate")

    builder.add_conditional_edges(
        "policy_gate",
        agent._route_after_policy,
        {
            "blocked": "response_composer",
            "defense": "defense_analyzer",
            "threat_intel": "threat_intel_analyzer",
            "redteam": "redteam_planner",
        },
    )

    builder.add_edge("defense_analyzer", "runbook_composer")
    builder.add_edge("threat_intel_analyzer", "runbook_composer")
    builder.add_edge("redteam_planner", "runbook_composer")
    builder.add_edge("runbook_composer", "response_composer")
    builder.add_edge("response_composer", END)

    return builder.compile()