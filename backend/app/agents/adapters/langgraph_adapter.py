def langgraph_capability() -> dict[str, object]:
    return {
        "framework": "LangGraph",
        "mode": "adapter_contract",
        "concepts": ["state graph", "checkpoints", "conditional edges", "retry paths"],
        "project_use": "Model Plan -> Search -> Analyze -> Report -> Evaluate as resumable graph nodes.",
        "production_rule": "Persist job state before every external tool boundary.",
    }
