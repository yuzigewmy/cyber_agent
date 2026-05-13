from __future__ import annotations

import math
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from cyber_agent_guarded.schemas import RetrievedContext


@dataclass
class RAGDocument:
    text: str
    metadata: dict[str, str] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9_.:/-]+", text.lower())


def parse_front_matter(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---"):
        return {}, raw
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, raw
    meta: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, parts[2].strip()


class InMemoryKnowledgeBase:
    """Small dependency-free retrieval layer for local demos and tests.

    Production deployments should replace this with a managed vector store or
    hybrid search engine. This class keeps the same returned context contract.
    """

    def __init__(self) -> None:
        self.documents: list[RAGDocument] = []
        self._doc_freq: dict[str, int] = {}
        self._dirty = True

    def add_documents(self, docs: Iterable[RAGDocument]) -> None:
        self.documents.extend(docs)
        self._dirty = True

    def _rebuild_stats(self) -> None:
        self._doc_freq = {}
        for doc in self.documents:
            for token in set(tokenize(doc.text)):
                self._doc_freq[token] = self._doc_freq.get(token, 0) + 1
        self._dirty = False

    def search(
        self,
        query: str,
        k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedContext]:
        if self._dirty:
            self._rebuild_stats()
        filters = filters or {}
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scored: list[tuple[float, RAGDocument]] = []
        total_docs = max(1, len(self.documents))
        for doc in self.documents:
            if not self._metadata_matches(doc.metadata, filters):
                continue
            doc_tokens = tokenize(doc.text)
            if not doc_tokens:
                continue
            term_counts: dict[str, int] = {}
            for token in doc_tokens:
                term_counts[token] = term_counts.get(token, 0) + 1
            score = 0.0
            for token in query_tokens:
                tf = term_counts.get(token, 0) / len(doc_tokens)
                if tf == 0:
                    continue
                idf = math.log((1 + total_docs) / (1 + self._doc_freq.get(token, 0))) + 1
                score += tf * idf
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        results: list[RetrievedContext] = []
        for score, doc in scored[:k]:
            results.append(
                RetrievedContext(
                    source=doc.metadata.get("source", doc.id),
                    collection=doc.metadata.get("collection", "default"),
                    sensitivity=doc.metadata.get("sensitivity", "internal"),
                    score=round(score, 6),
                    text=doc.text[:1800],
                )
            )
        return results

    @staticmethod
    def _metadata_matches(metadata: dict[str, str], filters: dict[str, Any]) -> bool:
        for key, value in filters.items():
            if key.endswith("__in"):
                field = key[:-4]
                allowed = set(str(v) for v in value)
                if str(metadata.get(field, "")) not in allowed:
                    return False
            elif key.endswith("__not"):
                field = key[:-5]
                if str(metadata.get(field, "")) == str(value):
                    return False
            elif str(metadata.get(key, "")) != str(value):
                return False
        return True


def split_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def load_markdown_dir(path: str | Path, collection: str, chunk_size: int = 1200) -> list[RAGDocument]:
    root = Path(path)
    docs: list[RAGDocument] = []
    if not root.exists():
        return docs
    for file_path in sorted(root.rglob("*.md")):
        raw = file_path.read_text(encoding="utf-8")
        metadata, body = parse_front_matter(raw)
        metadata.setdefault("source", str(file_path))
        metadata.setdefault("collection", collection)
        metadata.setdefault("sensitivity", "internal")
        for i, chunk in enumerate(split_text(body, chunk_size=chunk_size)):
            chunk_meta = dict(metadata)
            chunk_meta["chunk"] = str(i)
            docs.append(RAGDocument(text=chunk, metadata=chunk_meta))
    return docs


class OptionalLangChainChromaFactory:
    """Factory for a LangChain/Chroma retriever.

    It is isolated from the default path so unit tests can run without external
    services or API keys. Use this in production ingestion jobs after choosing
    the approved embedding provider.
    """

    @staticmethod
    def create_retriever(documents: list[RAGDocument], persist_dir: str = ".chroma"):
        try:
            from langchain_chroma import Chroma  # type: ignore
        except Exception:
            from langchain_community.vectorstores import Chroma  # type: ignore
        from langchain_core.documents import Document  # type: ignore
        from langchain_openai import OpenAIEmbeddings  # type: ignore

        lc_docs = [
            Document(page_content=doc.text, metadata=dict(doc.metadata, id=doc.id))
            for doc in documents
        ]
        embeddings = OpenAIEmbeddings()
        vector_store = Chroma.from_documents(
            documents=lc_docs,
            embedding=embeddings,
            persist_directory=persist_dir,
        )
        return vector_store.as_retriever(search_kwargs={"k": 6})
