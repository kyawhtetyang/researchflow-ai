from fastapi import APIRouter

from app.agents.adapters import langchain_capability, langgraph_capability, llamaindex_capability
from app.agents.openai_agents_runner import openai_agents_blueprint
from app.config import settings
from app.evals import evaluation_capability, tracing_capability
from app.rag import embedding_capability, indexing_capability, retrieval_capability

router = APIRouter()


@router.get("/")
def capabilities() -> dict[str, object]:
    return {
        "version": settings.app_version,
        "release": settings.app_version,
        "status": "hardening",
        "core": {
            "backend": ["FastAPI", "PostgreSQL", "pgvector", "Docker", "SQLAlchemy", "Alembic"],
            "workflow": ["LLM planner", "Tavily web search", "LLM summarizer", "LLM report generation", "citations"],
            "frontend": ["standalone ResearchFlow UI", "stored job history", "AI/ML Portfolio Ask integration"],
        },
        "agents": {
            "native": "Plan -> Search -> Analyze -> Report -> Evaluate",
            "openai_agents_sdk": openai_agents_blueprint(),
            "langgraph": langgraph_capability(),
            "llamaindex": llamaindex_capability(),
            "langchain": langchain_capability(),
        },
        "rag": {
            "embeddings": embedding_capability(),
            "indexing": indexing_capability(),
            "retrieval": retrieval_capability(),
        },
        "quality": {
            "evals": evaluation_capability(),
            "observability": tracing_capability(),
        },
    }
