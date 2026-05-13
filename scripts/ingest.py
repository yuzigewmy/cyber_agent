from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import typer
from rich.console import Console

from cyber_agent_guarded.config import load_settings
from cyber_agent_guarded.rag.ingest import build_in_memory_kb

app = typer.Typer(help="Validate local knowledge ingestion.")
console = Console()


@app.command()
def main(base_dir: Path = typer.Option(Path.cwd())) -> None:
    settings = load_settings(base_dir / "config" / "config.example.yaml")
    kb = build_in_memory_kb(settings.rag, base_dir=base_dir)
    console.print({"documents": len(kb.documents), "collections": list(settings.rag.collections)})


if __name__ == "__main__":
    app()
