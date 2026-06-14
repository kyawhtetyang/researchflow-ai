def llamaindex_capability() -> dict[str, object]:
    return {
        "framework": "LlamaIndex",
        "mode": "adapter_contract",
        "concepts": ["document connectors", "indexing", "query engines", "citation nodes"],
        "project_use": "Compare document-indexed research against pgvector-backed retrieval.",
        "production_rule": "Normalize citations into the internal Source model before reporting.",
    }
