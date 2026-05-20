from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from cyber_agent_guarded.tools.attack_mapping import AttackPathModeler
from cyber_agent_guarded.tools.runbook import RunbookComposer
from cyber_agent_guarded.tools.traffic import TrafficAnalyzer


class ToolLike(Protocol):
    pass


@dataclass(frozen=True)
class ToolDescriptor:
    name: str
    capability: str
    tool: ToolLike


class ToolRegistry:
    """Small service registry for security analysis tools.

    This keeps orchestration code decoupled from concrete tool constructors and
    gives the API a stable place to expose or audit enabled capabilities later.
    """

    def __init__(self, tools: list[ToolDescriptor] | None = None) -> None:
        self._tools: dict[str, ToolDescriptor] = {}
        for descriptor in tools or []:
            self.register(descriptor)

    def register(self, descriptor: ToolDescriptor) -> None:
        self._tools[descriptor.name] = descriptor

    def get(self, name: str) -> ToolLike:
        return self._tools[name].tool

    def capabilities(self) -> list[dict[str, str]]:
        return [
            {
                "name": descriptor.name,
                "capability": descriptor.capability,
            }
            for descriptor in self._tools.values()
        ]


def default_tool_registry() -> ToolRegistry:
    return ToolRegistry(
        [
            ToolDescriptor(
                name="traffic_analyzer",
                capability="HTTP/proxy evidence triage",
                tool=TrafficAnalyzer(),
            ),
            ToolDescriptor(
                name="runbook_composer",
                capability="Incident and exercise action planning",
                tool=RunbookComposer(),
            ),
            ToolDescriptor(
                name="attack_path_modeler",
                capability="High-level authorized exposure modeling",
                tool=AttackPathModeler(),
            ),
        ]
    )
