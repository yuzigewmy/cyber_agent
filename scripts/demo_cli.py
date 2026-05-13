from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import typer
from rich.console import Console

from cyber_agent_guarded.agent import CyberAgent
from cyber_agent_guarded.schemas import AgentMode, AgentRequest, ScopeApproval

app = typer.Typer(help="Run a local Cyber Agent Guarded demo.")
console = Console()


@app.command()
def main(
    mode: AgentMode = typer.Option(AgentMode.defense),
    question: str = typer.Option(...),
    asset: list[str] = typer.Option(None),
    evidence: Path | None = typer.Option(None),
    approved: bool = typer.Option(False),
) -> None:
    evidence_lines: list[str] = []
    if evidence and evidence.exists():
        evidence_lines = evidence.read_text(encoding="utf-8").splitlines()
    request = AgentRequest(
        mode=mode,
        question=question,
        assets=asset or [],
        evidence=evidence_lines,
        scope=ScopeApproval(approved=approved, approver="demo" if approved else None),
    )
    agent = CyberAgent(base_dir=str(Path(__file__).resolve().parents[1]))
    response = agent.handle(request)
    console.print_json(json.dumps(response.model_dump(), ensure_ascii=False))


if __name__ == "__main__":
    app()
