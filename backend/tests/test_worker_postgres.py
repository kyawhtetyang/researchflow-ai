import os
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.db import SessionLocal
from app.models.research_job import ResearchJob
from app import worker


pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").startswith("postgresql"),
    reason="requires PostgreSQL integration database",
)


def _insert_jobs(count: int) -> list[int]:
    db = SessionLocal()
    try:
        jobs = [ResearchJob(query=f"concurrency test job {i}", status="queued") for i in range(count)]
        db.add_all(jobs)
        db.commit()
        for job in jobs:
            db.refresh(job)
        return [job.id for job in jobs]
    finally:
        db.close()


def _claim_once():
    db = SessionLocal()
    try:
        job = worker._claim_next_job(db)
        return job.id if job is not None else None
    finally:
        db.close()


def _cleanup(job_ids: list[int]) -> None:
    db = SessionLocal()
    try:
        db.query(ResearchJob).filter(ResearchJob.id.in_(job_ids)).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def test_two_workers_claim_different_jobs_under_postgres():
    job_ids = _insert_jobs(2)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            claimed = list(pool.map(lambda _: _claim_once(), range(2)))

        assert None not in claimed
        assert len(set(claimed)) == 2
        assert set(claimed) == set(job_ids)
    finally:
        _cleanup(job_ids)


def test_two_workers_cannot_claim_same_single_job_under_postgres():
    job_ids = _insert_jobs(1)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            claimed = list(pool.map(lambda _: _claim_once(), range(2)))

        assert claimed.count(job_ids[0]) == 1
        assert claimed.count(None) == 1
    finally:
        _cleanup(job_ids)
