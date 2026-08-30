from __future__ import annotations

from app.services.web_search import search_web


def search_sources(query: str) -> list[dict]:
    topic = (query or "AI engineering research").strip()
    return search_web(topic)
