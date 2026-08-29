from app.models.report import Report
from app.models.research_job import ResearchJob
from app.models.research_step import ResearchStep
from app.models.source import Source
from app.services.errors import ResearchFlowError
from app.workflow import orchestrator


def _claimed_job(db_session) -> ResearchJob:
    job = ResearchJob(query="Research container transport efficiency", status="in_progress")
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


def test_workflow_completes_claimed_job_and_persists_artifacts(db_session, monkeypatch):
    job = _claimed_job(db_session)

    monkeypatch.setattr(orchestrator, "plan_research", lambda _: ["Plan", "Search", "Analyze", "Report"])
    monkeypatch.setattr(
        orchestrator,
        "search_sources",
        lambda _: [
            {
                "title": "Source A",
                "url": "https://example.com/a",
                "snippet": "Useful evidence",
                "content": "Detailed useful evidence",
                "score": 0.9,
            }
        ],
    )
    monkeypatch.setattr(
        orchestrator,
        "summarize_findings",
        lambda *_: [{"claim": "Efficiency can improve.", "evidence": "Evidence", "citation_numbers": [1]}],
    )
    monkeypatch.setattr(orchestrator, "generate_report", lambda *_: "# Report\n\nEvidence [Sources: 1]")
    monkeypatch.setattr(orchestrator, "score_source_quality", lambda _: 0.8)

    result = orchestrator.run_research_job(db_session, job)

    assert result.status == "completed"
    assert result.completed_at is not None
    assert db_session.query(ResearchStep).filter_by(job_id=job.id).count() == 4
    assert db_session.query(Source).filter_by(job_id=job.id).count() == 1
    assert db_session.query(Report).filter_by(job_id=job.id).count() == 1
    assert [step.agent_name for step in db_session.query(ResearchStep).filter_by(job_id=job.id).order_by(ResearchStep.step_order)] == [
        "planner",
        "researcher",
        "analyst",
        "reporter",
    ]


def test_workflow_rejects_unclaimed_job(db_session):
    job = ResearchJob(query="Should not execute", status="queued")
    db_session.add(job)
    db_session.commit()

    try:
        orchestrator.run_research_job(db_session, job)
    except ValueError as exc:
        assert "must be claimed" in str(exc)
    else:
        raise AssertionError("queued job executed without a worker claim")


def test_known_workflow_failure_marks_job_failed_and_rolls_back_partial_artifacts(db_session, monkeypatch):
    job = _claimed_job(db_session)

    monkeypatch.setattr(orchestrator, "plan_research", lambda _: ["Plan"])
    monkeypatch.setattr(
        orchestrator,
        "search_sources",
        lambda _: [
            {
                "title": "Partial source",
                "url": "https://example.com/partial",
                "snippet": "partial",
                "content": "partial",
                "score": 0.5,
            }
        ],
    )
    monkeypatch.setattr(orchestrator, "score_source_quality", lambda _: 0.5)

    class ExpectedFailure(ResearchFlowError):
        user_message = "Analysis provider unavailable."

    def fail_analysis(*_):
        raise ExpectedFailure()

    monkeypatch.setattr(orchestrator, "summarize_findings", fail_analysis)

    result = orchestrator.run_research_job(db_session, job)

    assert result.status == "failed"
    assert result.error == "Analysis provider unavailable."
    assert result.completed_at is not None
    assert db_session.query(ResearchStep).filter_by(job_id=job.id).count() == 0
    assert db_session.query(Source).filter_by(job_id=job.id).count() == 0
    assert db_session.query(Report).filter_by(job_id=job.id).count() == 0


def test_unexpected_workflow_failure_is_sanitized_and_rolls_back(db_session, monkeypatch):
    job = _claimed_job(db_session)
    monkeypatch.setattr(orchestrator, "plan_research", lambda _: (_ for _ in ()).throw(RuntimeError("secret failure detail")))

    result = orchestrator.run_research_job(db_session, job)

    assert result.status == "failed"
    assert result.error == "Unexpected research workflow failure."
    assert "secret" not in result.error
    assert db_session.query(ResearchStep).filter_by(job_id=job.id).count() == 0
