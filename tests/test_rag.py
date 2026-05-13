from cyber_agent_guarded.rag.document_store import InMemoryKnowledgeBase, RAGDocument


def test_search_returns_context() -> None:
    kb = InMemoryKnowledgeBase()
    kb.add_documents([
        RAGDocument(text="api gateway has WAF and Nginx ingress", metadata={"source": "arch", "collection": "architecture"}),
        RAGDocument(text="incident response preserve logs before containment", metadata={"source": "ir", "collection": "defense"}),
    ])
    results = kb.search("Nginx gateway WAF", k=1)
    assert results
    assert results[0].source == "arch"
