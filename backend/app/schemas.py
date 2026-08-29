from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

class ResearchJobCreate(BaseModel):
    query: str = Field(..., min_length=3)

class ResearchJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query: str
    status: str
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class ResearchStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    step_order: int
    agent_name: str
    status: str
    input: Optional[str] = None
    output: str
    created_at: datetime

class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    title: str
    url: str
    snippet: Optional[str] = None
    content: str
    score: Optional[float] = None
    quality_score: Optional[float] = None

class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    markdown: str
    created_at: datetime

class ResearchJobDetail(BaseModel):
    job: ResearchJobResponse
    steps: List[ResearchStepResponse]
    sources: List[SourceResponse]
    report: Optional[ReportResponse] = None

class ResearchJobSummary(BaseModel):
    job_id: int
    status: str
    step_count: int
    source_count: int
    average_source_quality: float
    has_report: bool
    readiness_score: float

class ResearchChatSource(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None
    quality_score: Optional[float] = None

class ResearchChatWorkflowStep(BaseModel):
    label: str
    status: str
    output: str

class ResearchChatResponse(BaseModel):
    job_id: int
    query: str
    status: str
    answer: str
    error: Optional[str] = None
    sources: List[ResearchChatSource]
    workflow: List[ResearchChatWorkflowStep]
    readiness_score: float

class EvalRunResponse(BaseModel):
    status: str
    total_jobs: int
    completed_jobs: int
    average_readiness_score: float
    checks: List[str]
