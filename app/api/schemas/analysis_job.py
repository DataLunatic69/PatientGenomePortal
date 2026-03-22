from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.database.models.analysis_job import JobStatus

class AnalysisJobCreate(BaseModel):
    dna_file_id: UUID

class AnalysisJobRead(BaseModel):
    id: UUID
    dna_file_id: UUID
    status: JobStatus
    current_step: str | None
    progress_pct: int
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}

class JobStatusUpdate(BaseModel):
    """Emitted as SSE event payload during job progress."""
    job_id: UUID
    status: JobStatus
    current_step: str | None
    progress_pct: int
    error_message: str | None
