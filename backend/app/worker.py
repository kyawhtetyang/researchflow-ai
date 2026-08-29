from __future__ import annotations

import signal
from threading import Event

from app.workflow.orchestrator import run_research_job
from app.config import settings
from app.db import SessionLocal
from app.models.research_job import ResearchJob

_shutdown = Event()


def _request_shutdown(*_: object) -> None:
    _shutdown.set()


def process_one() -> bool:
    db = SessionLocal()
    try:
        job = (
            db.query(ResearchJob)
            .filter(ResearchJob.status.in_(("queued", "pending")))
            .order_by(ResearchJob.created_at.asc())
            .with_for_update(skip_locked=True)
            .first()
        )
        if job is None:
            db.rollback()
            return False

        run_research_job(db, job)
        return True
    finally:
        db.close()


def main() -> None:
    signal.signal(signal.SIGTERM, _request_shutdown)
    signal.signal(signal.SIGINT, _request_shutdown)

    while not _shutdown.is_set():
        did_work = process_one()
        if _shutdown.is_set():
            break
        _shutdown.wait(0.2 if did_work else settings.worker_poll_interval)


if __name__ == "__main__":
    main()
