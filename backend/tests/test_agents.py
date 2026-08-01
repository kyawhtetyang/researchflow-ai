from app.agents.planner import plan_research
from app.agents.report_agent import generate_report
from app.agents.search_agent import search_sources
from app.agents.summarizer_agent import summarize_findings
from app.api.capabilities import capabilities
from app.api.research import _chat_status
from app.services import llm
from app.schemas import ResearchJobCreate


def test_research_agents_generate_a_source_backed_report(monkeypatch):
    query = "Research AI Engineer salaries in Singapore."

    monkeypatch.setattr(
        "app.agents.planner.generate_json",
        lambda **_: {
            "steps": [
                "Collect salary and hiring sources.",
                "Compare repeated role requirements.",
                "Summarize market patterns.",
                "Write the final recommendations.",
            ]
        },
    )
    monkeypatch.setattr(
        "app.agents.search_agent.search_web",
        lambda _: [
            {
                "title": "Example source",
                "url": "https://example.com/a",
                "snippet": "Python and FastAPI are commonly requested.",
                "content": "Python and FastAPI appear frequently in AI Engineer listings in Singapore.",
                "score": 0.91,
            },
            {
                "title": "Second source",
                "url": "https://example.com/b",
                "snippet": "Docker and deployment experience are valued.",
                "content": "Docker, APIs, and deployment experience appear in many postings.",
                "score": 0.84,
            },
        ],
    )
    monkeypatch.setattr(
        "app.agents.summarizer_agent.generate_json",
        lambda **_: {
            "findings": [
                {
                    "claim": "Python is a repeated requirement.",
                    "evidence": "It appears in both sample sources.",
                    "citation_numbers": [1, 2],
                },
                {
                    "claim": "Deployment skills matter.",
                    "evidence": "Docker and API operations are explicitly mentioned.",
                    "citation_numbers": [2],
                },
            ]
        },
    )
    monkeypatch.setattr(
        "app.agents.report_agent.generate_markdown",
        lambda **_: (
            "# Research Report: Research AI Engineer salaries in Singapore.\n\n"
            "## Executive Summary\n"
            "Demand centers on backend Python, APIs, and deployment skills. [Sources: 1, 2]\n\n"
            "## Research Plan\n"
            "1. Collect salary and hiring sources.\n\n"
            "## Findings\n"
            "- Python is a repeated requirement. [Sources: 1, 2]\n\n"
            "## Recommendations\n"
            "- Build projects that prove applied backend AI delivery. [Sources: 2]"
        ),
    )

    plan = plan_research(query)
    sources = search_sources(query)
    findings = summarize_findings(query, sources)
    report = generate_report(query, plan, findings, sources)

    assert len(plan) == 4
    assert len(sources) == 2
    assert findings[0]["citation_numbers"] == [1, 2]
    assert "## Executive Summary" in report
    assert "[Sources: 1, 2]" in report
    assert "## Sources" in report


def test_capabilities_expose_release_1_0_0():
    payload = capabilities()

    assert payload["version"] == "1.0.0"
    assert payload["release"] == "1.0.0"
    assert payload["status"] == "complete"
    assert payload["snapshot_line"] == "v3"
    assert "Tavily web search" in payload["core"]["workflow"]
    assert "stored job history" in payload["core"]["frontend"]
    assert payload["agents"]["openai_agents_sdk"]["framework"] == "OpenAI Agents SDK"


def test_research_api_is_async_first_and_chat_status_friendly():
    payload = ResearchJobCreate(query="What should ResearchFlow investigate next?")

    assert payload.run_now is False
    assert _chat_status("pending") == "queued"
    assert _chat_status("queued") == "queued"
    assert _chat_status("in_progress") == "thinking"
    assert _chat_status("completed") == "completed"
    assert _chat_status("failed") == "failed"


def test_llm_provider_order_supports_gemini_and_openai_compatible_fallback(monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_provider", "gemini")
    assert llm._provider_order() == ["gemini", "openai_compatible"]

    monkeypatch.setattr(llm.settings, "llm_provider", "openai_compatible")
    assert llm._provider_order() == ["openai_compatible", "gemini"]

    monkeypatch.setattr(llm.settings, "llm_provider", "auto")
    assert llm._provider_order() == ["gemini", "openai_compatible"]

#### alembic.ini
