from dataclasses import dataclass


@dataclass(frozen=True)
class AgentToolSpec:
    name: str
    purpose: str


def openai_agents_blueprint() -> dict[str, object]:
    """Framework-facing plan for a future OpenAI Agents SDK implementation."""
    tools = [
        AgentToolSpec("plan_research", "Break a question into evidence-seeking steps."),
        AgentToolSpec("search_sources", "Collect candidate sources with quality metadata."),
        AgentToolSpec("retrieve_memory", "Pull prior project and RAG context."),
        AgentToolSpec("write_report", "Produce a cited markdown research report."),
        AgentToolSpec("score_output", "Run deterministic quality checks."),
    ]
    return {
        "framework": "OpenAI Agents SDK",
        "mode": "adapter_contract",
        "handoffs": ["planner", "researcher", "analyst", "reporter", "evaluator"],
        "guardrails": ["source_required", "citation_required", "no_secret_output"],
        "tracing": ["job_id", "step_name", "tool_name", "latency_ms", "quality_score"],
        "tools": [tool.__dict__ for tool in tools],
    }
