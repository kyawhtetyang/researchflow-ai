from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.capabilities import router as capabilities_router
from app.api.eval import router as eval_router
from app.api.jobs import router as jobs_router
from app.api.reports import router as reports_router
from app.api.research import router as research_router
from app.config import settings

app = FastAPI(title="ResearchFlow AI API", version=settings.app_version)

_resolved_main = Path(__file__).resolve()
_frontend_source_candidates = [
    _resolved_main.parents[1] / "frontend",
    _resolved_main.parents[2] / "frontend" if len(_resolved_main.parents) > 2 else None,
]
_frontend_source_dir = next(
    (path for path in _frontend_source_candidates if path is not None and path.exists()),
    _resolved_main.parents[1] / "frontend",
)
_frontend_dist_dir = _frontend_source_dir / "dist"
_frontend_assets_dir = _frontend_dist_dir / "assets"

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research_router, prefix="/api/research", tags=["research"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["jobs"])
app.include_router(reports_router, prefix="/api/reports", tags=["reports"])
app.include_router(eval_router, prefix="/api/eval", tags=["eval"])
app.include_router(capabilities_router, prefix="/api/capabilities", tags=["capabilities"])

if _frontend_assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=_frontend_assets_dir), name="assets")


@app.get("/health")
def healthcheck():
    return {"status": "ok", "app": "ResearchFlow AI", "version": settings.app_version}


@app.get("/", response_class=FileResponse)
def frontend():
    if _frontend_dist_dir.exists():
        return FileResponse(_frontend_dist_dir / "index.html")
    return FileResponse(_frontend_source_dir / "index.html")
