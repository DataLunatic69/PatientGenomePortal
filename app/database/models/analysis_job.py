from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4

from sqlmodel import JSON, Column, Field, Relationship, SQLModel


class JobStatus(StrEnum):
    PENDING = "pending"
    PARSING = "parsing"
    ENRICHING = "enriching"
    SCORING = "scoring"
    RANKING = "ranking"
    EXPLAINING = "explaining"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisJob(SQLModel, table=True):
    __tablename__ = "analysis_jobs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    dna_file_id: UUID = Field(foreign_key="dna_files.id", index=True)
    status: JobStatus = Field(default=JobStatus.PENDING)

    # LangGraph state snapshot — stored as JSON
    graph_state: dict | None = Field(default=None, sa_column=Column(JSON))

    # progress tracking
    current_step: str | None = None
    progress_pct: int = Field(default=0, ge=0, le=100)
    error_message: str | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # relationships
    dna_file: "DnaFile" = Relationship(back_populates="analysis_jobs")
    variant_results: list["VariantResult"] = Relationship(back_populates="analysis_job")


from .dna_file import DnaFile  # noqa: E402
from .variant_result import VariantResult  # noqa: E402