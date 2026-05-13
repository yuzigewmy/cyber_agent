from __future__ import annotations

from pathlib import Path

from cyber_agent_guarded.config import RAGSettings
from cyber_agent_guarded.rag.document_store import InMemoryKnowledgeBase, load_markdown_dir


def build_in_memory_kb(settings: RAGSettings, base_dir: str | Path = ".") -> InMemoryKnowledgeBase:
    base = Path(base_dir)
    kb = InMemoryKnowledgeBase()
    for collection, rel_path in settings.collections.items():
        docs = load_markdown_dir(base / rel_path, collection=collection, chunk_size=settings.chunk_size)
        kb.add_documents(docs)
    return kb
