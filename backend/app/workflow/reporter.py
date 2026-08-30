from __future__ import annotations

import json

from app.services.llm import generate_markdown


def _sources_markdown(sources: list[dict]) -> str:
    lines = ["## Sources"]
    for idx, source in enumerate(sources, start=1):
        quality = float(source.get("quality_score", source.get("score", 0)) or 0)
        lines.append(
            f"{idx}. [{source['title']}]({source['url']}) - quality {quality:.2f}"
        )
    return "\n".join(lines)


def generate_report(query: str, plan: list[str], findings: list[dict], sources: list[dict]) -> str:
    prompt = (
        f"Research question:\n{query}\n\n"
        f"Plan:\n{json.dumps(plan, ensure_ascii=True, indent=2)}\n\n"
        f"Findings:\n{json.dumps(findings, ensure_ascii=True, indent=2)}\n\n"
        "Write a clear markdown report with these sections exactly:\n"
        "# Research Report: <query>\n"
        "## Executive Summary\n"
        "## Research Plan\n"
        "## Findings\n"
        "## Recommendations\n\n"
        "Use only the supplied findings and keep claims grounded in the cited sources. "
        "For every finding or recommendation, include inline citations like [Sources: 1, 3]. "
        "Do not add a Sources section because it will be appended separately."
    )
    markdown = generate_markdown(
        system_prompt="You are a precise research report writer who produces concise, evidence-based markdown.",
        user_prompt=prompt,
    ).strip()
    return f"{markdown}\n\n{_sources_markdown(sources)}"
