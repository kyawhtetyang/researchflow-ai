def langchain_capability() -> dict[str, object]:
    return {
        "framework": "LangChain",
        "mode": "adapter_contract",
        "concepts": ["retrievers", "tools", "LCEL", "structured output"],
        "project_use": "Compare chain-style research composition with the native orchestrator.",
        "production_rule": "Keep deterministic internal services as the source of truth.",
    }
