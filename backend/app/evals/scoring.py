def evaluation_capability() -> dict[str, object]:
    return {
        "component": "evaluation",
        "metrics": ["readiness_score", "source_count", "citation_coverage", "step_completion"],
        "regression_checks": ["minimum_sources", "report_sections", "no_empty_steps"],
        "reason": "Recruiter-ready AI systems need measurable output quality.",
    }
