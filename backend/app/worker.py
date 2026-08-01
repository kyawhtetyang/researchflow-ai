from __future__ import annotations

import time

from app.agents.orchestrator import run_research_job
from app.config import settings
from app.db import SessionLocal
from app.models.research_job import ResearchJob


def process_one() -> bool:
    db = SessionLocal()
    try:
        job = (
            db.query(ResearchJob)
            .filter(ResearchJob.status.in_(("queued", "pending")))
            .order_by(ResearchJob.created_at.asc())
            .first()
        )
        if job is None:
            return False
        run_research_job(db, job)
        return True
    finally:
        db.close()


def main() -> None:
    while True:
        did_work = process_one()
        time.sleep(0.2 if did_work else settings.worker_poll_interval)


if __name__ == "__main__":
    main()
