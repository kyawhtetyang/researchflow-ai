from __future__ import annotations

from app.services.errors import GenerationError
from app.services.llm import generate_json


def plan_research(query: str) -> list[str]:
    topic = (query or "").strip()
    if not topic:
        return []

    payload = generate_json(
        system_prompt=(
            "You are a research planning assistant. "
            "Return valid JSON with a single key named steps. "
            "steps must be an ordered array of 4 to 6 short action-oriented strings."
        ),
        user_prompt=(
            f"Create a focused research plan for this question:\n{topic}\n\n"
            "The plan should cover source discovery, comparison, analysis, and a final recommendation."
        ),
    )

    if not isinstance(payload, dict) or not isinstance(payload.get("steps"), list):
        raise GenerationError("Planner returned an invalid response structure.")

    steps = [str(item).strip() for item in payload["steps"] if str(item).strip()]
    if len(steps) < 3:
        raise GenerationError("Planner returned too few meaningful research steps.")
    return steps[:6]
