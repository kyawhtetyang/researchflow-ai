from app.api.capabilities import capabilities


def test_capabilities_report_active_runtime_only():
    payload = capabilities()

    assert payload["status"] == "stable"
    assert payload["runtime"]["workflow"] == ["plan", "research", "analyze", "report"]
    assert "Gemini" in payload["runtime"]["providers"]
    assert "Tavily web search" in payload["runtime"]["providers"]
    assert "agents" not in payload
    assert "rag" not in payload
    assert payload["future"]["documentation"] == "docs/future/frameworks-and-rag.md"
