from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.report import Report
from app.models.research_job import ResearchJob
from app.models.research_step import ResearchStep
from app.models.source import Source
from app.readiness import readiness_score
from app.schemas import EvalRunResponse

router = APIRouter()


@router.post("/run", response_model=EvalRunResponse)
def run_eval(db: Session = Depends(get_db)):
    jobs = db.query(ResearchJob).all()
    checks: list[str] = []
    scores: list[float] = []

    for job in jobs:
        step_count = db.query(ResearchStep).filter(ResearchStep.job_id == job.id).count()
        source_count = db.query(Source).filter(Source.job_id == job.id).count()
        has_report = db.query(Report).filter(Report.job_id == job.id).first() is not None
        scores.append(readiness_score(job, step_count, source_count, has_report))
        checks.append(f"job {job.id}: status={job.status}, steps={step_count}, sources={source_count}, report={has_report}")

    completed = sum(1 for job in jobs if job.status == "completed")
    average = sum(scores) / len(scores) if scores else 0.0
    return EvalRunResponse(
        status="done",
        total_jobs=len(jobs),
        completed_jobs=completed,
        average_readiness_score=round(average, 3),
        checks=checks,
    )
