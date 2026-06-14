def tracing_capability() -> dict[str, object]:
    return {
        "component": "observability",
        "events": ["job_created", "step_started", "tool_called", "report_written", "eval_scored"],
        "fields": ["job_id", "step", "status", "latency_ms", "quality_score"],
        "reason": "Trace shape is defined now so LangSmith, OpenAI tracing, or custom tables can plug in later.",
    }
