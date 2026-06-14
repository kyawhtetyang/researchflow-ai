from app.agents.planner import plan_research
from app.agents.report_agent import generate_report
from app.agents.search_agent import search_sources
from app.agents.summarizer_agent import summarize_findings
from app.api.capabilities import capabilities


def test_research_agents_generate_a_recruiter_ready_report():
    query = "What AI Engineer project should follow a production RAG assistant?"

    plan = plan_research(query)
    sources = search_sources(query)
    findings = summarize_findings(query, sources)
    report = generate_report(query, plan, findings, sources)

    assert len(plan) >= 5
    assert len(sources) >= 5
    assert len(findings) >= 4
    assert "ResearchFlow AI" in report
    assert "Recruiter-Facing Proof" in report
    assert "OpenAI Agents SDK" in report


def test_v2_capabilities_expose_framework_contracts():
    payload = capabilities()

    assert payload["version"] == "2.0.0"
    assert payload["agents"]["openai_agents_sdk"]["framework"] == "OpenAI Agents SDK"
    assert payload["agents"]["langgraph"]["framework"] == "LangGraph"
    assert payload["agents"]["llamaindex"]["framework"] == "LlamaIndex"
    assert payload["agents"]["langchain"]["framework"] == "LangChain"
    assert "pgvector" in payload["core"]["backend"]
    assert "AI/ML Portfolio Ask integration" in payload["core"]["frontend"]
