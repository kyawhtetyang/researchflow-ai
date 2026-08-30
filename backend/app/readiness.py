from app.models.research_job import ResearchJob


def readiness_score(job: ResearchJob, step_count: int, source_count: int, has_report: bool) -> float:
    score = 0.0
    score += 0.25 if job.status == "completed" else 0.0
    score += min(step_count / 4, 1.0) * 0.25
    score += min(source_count / 5, 1.0) * 0.25
    score += 0.25 if has_report else 0.0
    return round(score, 3)
