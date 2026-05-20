# Project Optimization Plan

## References

The project is closest to three mature open-source patterns:

- Dify: separates API, service, workflow orchestration, model provider adapters, and persistence so application features can evolve independently.
- Open WebUI: keeps a clean web/API boundary, exposes runtime capabilities, and treats model connectivity as an adapter rather than the whole application.
- MITRE Caldera and LangGraph: model security operations as explicit stages with auditable routing, tools, and approval gates.

## Current Findings

- `app/main.py` mixed application bootstrap, dependency construction, auth endpoints, chat endpoints, and persistence orchestration.
- `CyberAgent` directly constructed every tool, which made adding or auditing tools harder.
- Responses did not expose enough runtime trace information for debugging or UI inspection.
- Several user-facing Chinese strings were mojibake, making fallback output and policy messages hard to read.

## Optimization Direction

1. Split API routing by domain.
   Auth, chat, and system endpoints should live behind independent routers.

2. Add an application factory.
   Startup, CORS, settings, and router registration should be centralized in `create_app()`.

3. Add a service layer.
   Chat request handling should coordinate agent execution and persistence outside the route handler.

4. Add a tool registry.
   The orchestrator should depend on named capabilities instead of directly creating every tool.

5. Make runtime capabilities observable.
   Add a capabilities endpoint and response trace data showing graph nodes, tools, model fallback state, and policy decisions.

6. Keep local-first execution.
   The project should still run without API keys using in-memory RAG, SQLite, local rules, and deterministic fallback answers.

## Implemented Changes

- Added `cyber_agent_guarded.app_factory.create_app`.
- Added API routers under `cyber_agent_guarded.api`.
- Added `ChatService` for agent execution plus persistence.
- Added `ToolRegistry` and default security tool descriptors.
- Added `/v1/system/capabilities`.
- Added `AgentResponse.trace`.
- Restored readable Chinese fallback and safety prompt text.
