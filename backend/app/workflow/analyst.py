from __future__ import annotations

from app.services.errors import GenerationError
from app.services.llm import generate_json


def _build_source_context(sources: list[dict]) -> str:
    blocks = []
    for idx, source in enumerate(sources, start=1):
        content = str(source.get("content") or source.get("snippet") or "").strip()
        blocks.append(
            f"[{idx}] {source.get('title')}\n"
            f"URL: {source.get('url')}\n"
            f"Snippet: {source.get('snippet')}\n"
            f"Content: {content[:1800]}"
        )
    return "\n\n".join(blocks)


def summarize_findings(query: str, sources: list[dict]) -> list[dict]:
    payload = generate_json(
        system_prompt=(
            "You are a research analyst. "
            "Return valid JSON with one key named findings. "
            "findings must be an array of 3 to 6 objects. "
            "Each object must contain claim, evidence, and citation_numbers. "
            "citation_numbers must be an array of source numbers that directly support the claim."
        ),
        user_prompt=(
            f"Research question:\n{query}\n\n"
            f"Sources:\n{_build_source_context(sources)}\n\n"
            "Extract the strongest factual findings only from these sources."
        ),
    )

    if not isinstance(payload, dict) or not isinstance(payload.get("findings"), list):
        raise GenerationError("Summarizer returned an invalid response structure.")

    findings = []
    source_count = len(sources)
    for raw in payload["findings"]:
        if not isinstance(raw, dict):
            continue
        claim = str(raw.get("claim") or "").strip()
        evidence = str(raw.get("evidence") or "").strip()
        citations = []
        for value in raw.get("citation_numbers", []):
            try:
                number = int(value)
            except (TypeError, ValueError):
                continue
            if 1 <= number <= source_count and number not in citations:
                citations.append(number)
        if claim and citations:
            findings.append(
                {
                    "claim": claim,
                    "evidence": evidence,
                    "citation_numbers": citations,
                }
            )

    if not findings:
        raise GenerationError("Summarizer did not return any usable findings.")

    return findings[:6]
