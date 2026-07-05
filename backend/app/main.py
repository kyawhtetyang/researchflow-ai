from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.api.capabilities import router as capabilities_router
from app.api.eval import router as eval_router
from app.api.jobs import router as jobs_router
from app.api.reports import router as reports_router
from app.api.research import router as research_router
from app.db import Base, engine
from app import models  # noqa: F401

app = FastAPI(title="ResearchFlow AI API", version="1.0.0")

_resolved_main = Path(__file__).resolve()
_frontend_candidates = [_resolved_main.parents[1] / "frontend"]
if len(_resolved_main.parents) > 3:
    _frontend_candidates.append(_resolved_main.parents[3] / "frontend")
FRONTEND_DIR = next((path for path in _frontend_candidates if path.exists()), _frontend_candidates[0])

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research_router, prefix="/api/research", tags=["research"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["jobs"])
app.include_router(reports_router, prefix="/api/reports", tags=["reports"])
app.include_router(eval_router, prefix="/api/eval", tags=["eval"])
app.include_router(capabilities_router, prefix="/api/capabilities", tags=["capabilities"])

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/health")
def healthcheck():
    return {"status": "ok", "app": "ResearchFlow AI", "version": "1.0.0"}

@app.get("/", response_class=FileResponse)
def frontend():
    return FileResponse(FRONTEND_DIR / "index.html")
