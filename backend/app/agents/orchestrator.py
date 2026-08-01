from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.agents.planner import plan_research
from app.agents.report_agent import generate_report
from app.agents.search_agent import search_sources
from app.agents.summarizer_agent import summarize_findings
from app.models.report import Report
from app.models.research_job import ResearchJob
from app.models.research_step import ResearchStep
from app.models.source import Source
from app.db import SessionLocal
from app.services.citations import score_source_quality
from app.services.errors import ResearchFlowError


def _add_step(db: Session, job_id: int, order: int, agent_name: str, input_text: str, output_text: str) -> None:
    db.add(
        ResearchStep(
            job_id=job_id,
            step_order=order,
            agent_name=agent_name,
            status="completed",
            input=input_text,
            output=output_text,
        )
    )


def _format_findings(findings: list[dict]) -> str:
    lines = []
    for idx, finding in enumerate(findings, start=1):
        citations = ", ".join(str(number) for number in finding.get("citation_numbers", []))
        lines.append(f"{idx}. {finding['claim']} [Sources: {citations}]")
        if finding.get("evidence"):
            lines.append(f"Evidence: {finding['evidence']}")
    return "\n".join(lines)


def run_research_job(db: Session, job: ResearchJob) -> ResearchJob:
    job.status = "in_progress"
    job.started_at = datetime.utcnow()
    db.commit()
    db.refresh(job)

    try:
        plan = plan_research(job.query)
        _add_step(db, job.id, 1, "planner", job.query, "\n".join(plan))

        raw_sources = search_sources(job.query)
        sources = []
        for raw in raw_sources:
            quality = score_source_quality(raw)
            raw["quality_score"] = quality
            source = Source(
                job_id=job.id,
                title=raw["title"],
                url=raw["url"],
                snippet=raw["snippet"],
                content=raw["content"],
                score=raw["score"],
                quality_score=quality,
            )
            db.add(source)
            sources.append(raw)
        _add_step(db, job.id, 2, "search_agent", job.query, "\n".join(f"- {s['title']} ({s['url']})" for s in sources))

        findings = summarize_findings(job.query, sources)
        _add_step(db, job.id, 3, "analysis_agent", "\n".join(s["content"] for s in sources), _format_findings(findings))

        markdown = generate_report(job.query, plan, findings, sources)
        report = Report(job_id=job.id, markdown=markdown)
        db.add(report)
        _add_step(db, job.id, 4, "report_agent", job.query, markdown)

        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job
    except ResearchFlowError as exc:
        job.status = "failed"
        job.error = exc.user_message
        job.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job
    except Exception:
        job.status = "failed"
        job.error = "Unexpected research workflow failure."
        job.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job


def run_research_job_by_id(job_id: int) -> None:
    db = SessionLocal()
    try:
        job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if job is None:
            return
        if (job.status or "").strip().lower() not in {"queued", "pending"}:
            return
        run_research_job(db, job)
    finally:
        db.close()
