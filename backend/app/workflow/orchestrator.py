from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.workflow.planner import plan_research
from app.workflow.reporter import generate_report
from app.workflow.researcher import search_sources
from app.workflow.analyst import summarize_findings
from app.models.report import Report
from app.models.research_job import ResearchJob
from app.models.research_step import ResearchStep
from app.models.source import Source
from app.services.citations import score_source_quality
from app.services.errors import ResearchFlowError

logger = logging.getLogger(__name__)


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
    """Execute a job that has already been atomically claimed by the worker."""
    if (job.status or "").strip().lower() != "in_progress":
        raise ValueError("research job must be claimed before workflow execution")

    try:
        logger.info("Job id=%s stage=planner started", job.id)
        plan = plan_research(job.query)
        _add_step(db, job.id, 1, "planner", job.query, "\n".join(plan))
        logger.info("Job id=%s stage=planner completed", job.id)

        logger.info("Job id=%s stage=researcher started", job.id)
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
        _add_step(db, job.id, 2, "researcher", job.query, "\n".join(f"- {s['title']} ({s['url']})" for s in sources))
        logger.info("Job id=%s stage=researcher completed sources=%s", job.id, len(sources))

        logger.info("Job id=%s stage=analyst started", job.id)
        findings = summarize_findings(job.query, sources)
        _add_step(db, job.id, 3, "analyst", "\n".join(s["content"] for s in sources), _format_findings(findings))
        logger.info("Job id=%s stage=analyst completed findings=%s", job.id, len(findings))

        logger.info("Job id=%s stage=reporter started", job.id)
        markdown = generate_report(job.query, plan, findings, sources)
        report = Report(job_id=job.id, markdown=markdown)
        db.add(report)
        _add_step(db, job.id, 4, "reporter", job.query, markdown)
        logger.info("Job id=%s stage=reporter completed", job.id)

        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        logger.info("Job id=%s workflow completed", job.id)
        return job
    except ResearchFlowError as exc:
        logger.warning("Job id=%s workflow failed: %s", job.id, exc.user_message)
        db.rollback()
        job = db.query(ResearchJob).filter(ResearchJob.id == job.id).first()
        if job is None:
            raise
        job.status = "failed"
        job.error = exc.user_message
        job.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job
    except Exception:
        logger.exception("Job id=%s workflow failed unexpectedly", job.id)
        db.rollback()
        job = db.query(ResearchJob).filter(ResearchJob.id == job.id).first()
        if job is None:
            raise
        job.status = "failed"
        job.error = "Unexpected research workflow failure."
        job.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job
