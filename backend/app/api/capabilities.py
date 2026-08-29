from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/")
def capabilities() -> dict[str, object]:
    return {
        "version": settings.app_version,
        "release": settings.app_version,
        "status": "architecture_refactor",
        "runtime": {
            "api": ["FastAPI"],
            "database": ["PostgreSQL", "SQLAlchemy", "Alembic"],
            "worker": ["database-backed queued jobs", "single-job polling worker"],
            "workflow": ["plan", "research", "analyze", "report"],
            "providers": ["Gemini", "OpenAI-compatible LLM", "Tavily web search"],
            "quality": ["source quality scoring", "inline citations", "readiness evaluation"],
            "frontend": ["ResearchFlow UI", "stored job history"],
        },
        "future": {
            "documentation": "docs/future/frameworks-and-rag.md",
            "note": "Framework adapters and RAG are roadmap concepts, not active runtime capabilities.",
        },
    }
