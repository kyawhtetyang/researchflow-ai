def indexing_capability() -> dict[str, object]:
    return {
        "component": "indexer",
        "stores": ["PostgreSQL", "pgvector"],
        "pipeline": ["load", "chunk", "embed", "upsert", "verify_citations"],
        "reason": "Make ingestion auditable before research jobs consume documents.",
    }
