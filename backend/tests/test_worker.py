from app.models.research_job import ResearchJob
from app import worker


def _queued_job(db_session, query: str = "Investigate worker behavior") -> ResearchJob:
    job = ResearchJob(query=query, status="queued")
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


def test_claim_next_job_moves_oldest_queued_job_to_in_progress(db_session):
    first = _queued_job(db_session, "first queued job")
    second = _queued_job(db_session, "second queued job")

    claimed = worker._claim_next_job(db_session)

    assert claimed is not None
    assert claimed.id == first.id
    assert claimed.status == "in_progress"
    assert claimed.started_at is not None

    db_session.refresh(second)
    assert second.status == "queued"


def test_claim_next_job_does_not_reclaim_in_progress_job(db_session):
    job = _queued_job(db_session)
    first_claim = worker._claim_next_job(db_session)
    second_claim = worker._claim_next_job(db_session)

    assert first_claim.id == job.id
    assert second_claim is None


def test_process_one_commits_claim_before_workflow_runs(db_session, session_factory, monkeypatch):
    job = _queued_job(db_session)
    observed = {}

    monkeypatch.setattr(worker, "SessionLocal", session_factory)

    def fake_run_research_job(db, claimed_job):
        verifier = session_factory()
        try:
            persisted = verifier.query(ResearchJob).filter(ResearchJob.id == claimed_job.id).one()
            observed["status"] = persisted.status
            observed["started_at"] = persisted.started_at
        finally:
            verifier.close()

        claimed_job.status = "completed"
        db.commit()
        return claimed_job

    monkeypatch.setattr(worker, "run_research_job", fake_run_research_job)

    assert worker.process_one() is True
    assert observed["status"] == "in_progress"
    assert observed["started_at"] is not None

    db_session.expire_all()
    persisted = db_session.query(ResearchJob).filter(ResearchJob.id == job.id).one()
    assert persisted.status == "completed"


def test_process_one_returns_false_when_queue_is_empty(db_session, session_factory, monkeypatch):
    monkeypatch.setattr(worker, "SessionLocal", session_factory)
    assert worker.process_one() is False
