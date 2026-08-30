from __future__ import annotations

import logging
import signal
from datetime import datetime
from threading import Event

from app.workflow.orchestrator import run_research_job
from app.config import settings
from app.db import SessionLocal
from app.models.research_job import ResearchJob

logger = logging.getLogger(__name__)
_shutdown = Event()


def _request_shutdown(*_: object) -> None:
    logger.info("Worker shutdown requested")
    _shutdown.set()


def _claim_next_job(db):
    job = (
        db.query(ResearchJob)
        .filter(ResearchJob.status == "queued")
        .order_by(ResearchJob.created_at.asc())
        .with_for_update(skip_locked=True)
        .first()
    )
    if job is None:
        db.rollback()
        return None

    # Claim ownership while the row lock is held, then commit the claim before
    # running slow external LLM/search work. Other workers can only select jobs
    # that remain in the queued state.
    job.status = "in_progress"
    job.started_at = datetime.utcnow()
    job.error = None
    db.commit()
    db.refresh(job)
    logger.info("Claimed research job id=%s", job.id)
    return job


def process_one() -> bool:
    db = SessionLocal()
    try:
        job = _claim_next_job(db)
        if job is None:
            return False

        logger.info("Starting research job id=%s", job.id)
        result = run_research_job(db, job)
        logger.info("Finished research job id=%s status=%s", result.id, result.status)
        return True
    except Exception:
        logger.exception("Worker failed while processing a research job")
        raise
    finally:
        db.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    signal.signal(signal.SIGTERM, _request_shutdown)
    signal.signal(signal.SIGINT, _request_shutdown)
    logger.info("ResearchFlow worker started poll_interval=%ss", settings.worker_poll_interval)

    while not _shutdown.is_set():
        did_work = process_one()
        if _shutdown.is_set():
            break
        _shutdown.wait(0.2 if did_work else settings.worker_poll_interval)

    logger.info("ResearchFlow worker stopped")


if __name__ == "__main__":
    main()
