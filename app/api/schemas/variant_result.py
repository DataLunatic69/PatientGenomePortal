from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.database.models.variant_result import PathogenicityLabel

class VariantResultRead(BaseModel):
    id: UUID
    analysis_job_id: UUID
    chromosome: str
    position: int
    reference_bases: str
    alternate_bases: str
    gene_name: str | None
    gene_id: str | None
    delta_scores: dict | None
    splicing_score: float | None
    rank_score: float | None
    rank_position: int | None
    clinvar_id: str | None
    clinvar_classification: PathogenicityLabel | None
    clinvar_review_status: str | None
    gemini_summary: str | None
    gemini_risk_level: str | None
    top_tissues_affected: list[str] | None

    model_config = {"from_attributes": True}

class VariantResultPage(BaseModel):
    """Paginated variant results."""
    total: int
    page: int
    page_size: int
    items: list[VariantResultRead]


class ChatMessage(BaseModel):
    role: str
    content: str


class ResultsChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = Field(default_factory=list)


class ResultsChatResponse(BaseModel):
    answer: str
