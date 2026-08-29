from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.workflow.orchestrator import run_research_job_by_id
from app.schemas import ResearchChatResponse, ResearchJobCreate, ResearchJobDetail, ResearchJobResponse, ResearchJobSummary
from app.models.report import Report
from app.models.research_job import ResearchJob
from app.models.research_step import ResearchStep
from app.models.source import Source

router = APIRouter()


def _chat_status(status: str) -> str:
    normalized = (status or "").strip().lower()
    if normalized in {"pending", "queued"}:
        return "queued"
    if normalized == "in_progress":
        return "thinking"
    if normalized in {"completed", "failed"}:
        return normalized
    return normalized or "queued"


def _readiness_score(job: ResearchJob, step_count: int, source_count: int, has_report: bool) -> float:
    readiness = 0.0
    readiness += 0.25 if job.status == "completed" else 0
    readiness += min(step_count / 4, 1.0) * 0.25
    readiness += min(source_count / 5, 1.0) * 0.25
    readiness += 0.25 if has_report else 0
    return round(readiness, 3)


def _get_research_parts(job_id: int, db: Session):
    job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="research job not found")

    steps = (
        db.query(ResearchStep)
        .filter(ResearchStep.job_id == job_id)
        .order_by(ResearchStep.step_order.asc(), ResearchStep.id.asc())
        .all()
    )
    sources = db.query(Source).filter(Source.job_id == job_id).order_by(Source.quality_score.desc()).all()
    report = db.query(Report).filter(Report.job_id == job_id).order_by(Report.id.desc()).first()
    return job, steps, sources, report


@router.get("/", response_model=list[ResearchJobResponse])
def list_research_jobs(db: Session = Depends(get_db)):
    return db.query(ResearchJob).order_by(ResearchJob.created_at.desc()).limit(25).all()


@router.post("/", response_model=ResearchJobResponse)
def create_research_job(
    job_in: ResearchJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = ResearchJob(query=job_in.query, status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)

    if job_in.run_now:
        background_tasks.add_task(run_research_job_by_id, job.id)

    return job


@router.get("/{job_id}", response_model=ResearchJobDetail)
def get_research_job(job_id: int, db: Session = Depends(get_db)):
    job, steps, sources, report = _get_research_parts(job_id, db)
    return {"job": job, "steps": steps, "sources": sources, "report": report}


@router.get("/{job_id}/chat", response_model=ResearchChatResponse)
def get_research_chat(job_id: int, db: Session = Depends(get_db)):
    job, steps, sources, report = _get_research_parts(job_id, db)
    status = _chat_status(job.status)
    if status == "completed" and report is not None:
        answer = report.markdown
    elif status == "failed":
        answer = job.error or "Research job failed before a report could be created."
    elif status == "thinking":
        answer = "ResearchFlow is planning, gathering sources, analyzing evidence, and preparing the report."
    else:
        answer = "ResearchFlow accepted the research job and will start processing shortly."

    return {
        "job_id": job.id,
        "query": job.query,
        "status": status,
        "answer": answer,
        "error": job.error,
        "sources": [
            {
                "title": source.title,
                "url": source.url,
                "snippet": source.snippet,
                "quality_score": source.quality_score,
            }
            for source in sources
        ],
        "workflow": [
            {
                "label": step.agent_name,
                "status": step.status,
                "output": step.output,
            }
            for step in steps
        ],
        "readiness_score": _readiness_score(job, len(steps), len(sources), report is not None),
    }


@router.get("/{job_id}/summary", response_model=ResearchJobSummary)
def get_research_summary(job_id: int, db: Session = Depends(get_db)):
    job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="research job not found")

    step_count = db.query(ResearchStep).filter(ResearchStep.job_id == job_id).count()
    sources = db.query(Source).filter(Source.job_id == job_id).all()
    report = db.query(Report).filter(Report.job_id == job_id).first()
    source_count = len(sources)
    avg_quality = sum(float(s.quality_score or 0) for s in sources) / source_count if source_count else 0.0
    return ResearchJobSummary(
        job_id=job.id,
        status=job.status,
        step_count=step_count,
        source_count=source_count,
        average_source_quality=round(avg_quality, 3),
        has_report=report is not None,
        readiness_score=_readiness_score(job, step_count, source_count, report is not None),
    )
