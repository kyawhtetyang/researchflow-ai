from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.research_job import ResearchJob
from app.models.research_step import ResearchStep
from app.schemas import ResearchJobResponse, ResearchStepResponse

router = APIRouter()


def _require_job(job_id: int, db: Session) -> ResearchJob:
    job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@router.get("/", response_model=list[ResearchJobResponse])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(ResearchJob).order_by(ResearchJob.created_at.desc()).limit(25).all()


@router.get("/{job_id}", response_model=ResearchJobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    return _require_job(job_id, db)


@router.get("/{job_id}/steps", response_model=list[ResearchStepResponse])
def get_job_steps(job_id: int, db: Session = Depends(get_db)):
    _require_job(job_id, db)
    return (
        db.query(ResearchStep)
        .filter(ResearchStep.job_id == job_id)
        .order_by(ResearchStep.step_order.asc(), ResearchStep.id.asc())
        .all()
    )
