import pytest
from fastapi import HTTPException

from app.api import jobs, reports, research
from app.models.research_job import ResearchJob
from app.schemas import ResearchJobCreate


def test_create_research_job_enqueues_only(db_session):
    created = research.create_research_job(
        ResearchJobCreate(query="Investigate current logistics bottlenecks"),
        db_session,
    )

    assert created.status == "queued"
    assert created.started_at is None
    assert created.completed_at is None


def test_job_steps_404_when_parent_job_missing(db_session):
    with pytest.raises(HTTPException) as exc_info:
        jobs.get_job_steps(999999, db_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "job not found"


def test_report_sources_404_when_parent_job_missing(db_session):
    with pytest.raises(HTTPException) as exc_info:
        reports.get_sources(999999, db_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "job not found"


def test_report_route_distinguishes_existing_job_without_report(db_session):
    job = ResearchJob(query="Existing job without report", status="queued")
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    with pytest.raises(HTTPException) as exc_info:
        reports.get_report(job.id, db_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "report not found"


def test_research_chat_maps_runtime_states(db_session):
    assert research._chat_status("queued") == "queued"
    assert research._chat_status("in_progress") == "thinking"
    assert research._chat_status("completed") == "completed"
    assert research._chat_status("failed") == "failed"
