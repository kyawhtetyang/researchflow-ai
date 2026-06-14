def embedding_capability() -> dict[str, object]:
    return {
        "component": "embeddings",
        "default_provider": "hash",
        "upgrade_path": ["OpenAI embeddings", "sentence-transformers", "hybrid BM25 + vector"],
        "reason": "Keep local verification deterministic while exposing production RAG design.",
    }
