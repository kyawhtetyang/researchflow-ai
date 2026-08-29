from datetime import datetime

from sqlalchemy import CheckConstraint, Column, DateTime, Integer, String, Text

from app.db import Base


class ResearchJob(Base):
    __tablename__ = "research_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'in_progress', 'completed', 'failed')",
            name="ck_research_jobs_status",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="queued")
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
