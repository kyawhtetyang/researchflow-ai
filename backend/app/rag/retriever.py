def retrieval_capability() -> dict[str, object]:
    return {
        "component": "retriever",
        "strategies": ["semantic", "keyword", "source_quality_rerank"],
        "outputs": ["source_id", "title", "url", "excerpt", "quality_score"],
        "reason": "Reports should show where claims came from, not only produce text.",
    }
