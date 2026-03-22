from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class UploadResponse(BaseModel):
    """Returned after a DNA file is uploaded and job is enqueued."""
    dna_file_id: UUID
    job_id: UUID
    message: str

class ReportRead(BaseModel):
    job_id: UUID
    gemini_report: str
    total_variants_analyzed: int
    high_risk_count: int
    moderate_risk_count: int
