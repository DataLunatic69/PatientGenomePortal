from enum import StrEnum
from uuid import UUID, uuid4

from sqlmodel import JSON, Column, Field, Relationship, SQLModel


class PathogenicityLabel(StrEnum):
    PATHOGENIC = "pathogenic"
    LIKELY_PATHOGENIC = "likely_pathogenic"
    VUS = "vus"
    LIKELY_BENIGN = "likely_benign"
    BENIGN = "benign"
    UNKNOWN = "unknown"


class VariantResult(SQLModel, table=True):
    __tablename__ = "variant_results"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    analysis_job_id: UUID = Field(foreign_key="analysis_jobs.id", index=True)

    # ── Variant coordinates ───────────────────────────────────────────────────
    chromosome: str = Field(max_length=10)       # e.g. "chr17"
    position: int                                 # 1-based hg38
    reference_bases: str = Field(max_length=512)
    alternate_bases: str = Field(max_length=512)
    gene_name: str | None = Field(default=None, max_length=64)
    gene_id: str | None = Field(default=None, max_length=64)  # Ensembl ID

    # ── AlphaGenome scores ────────────────────────────────────────────────────
    # {"RNA_SEQ": {"breast": -2.3, "ovary": -1.8}, "ATAC": {...}, ...}
    delta_scores: dict | None = Field(default=None, sa_column=Column(JSON))
    # merged splicing: splice_sites + splice_site_usage + junctions/5
    splicing_score: float | None = None
    # 0–1 aggregate rank score, higher = more concerning
    rank_score: float | None = None
    rank_position: int | None = None             # 1 = most concerning variant

    # ── ClinVar ───────────────────────────────────────────────────────────────
    clinvar_id: str | None = Field(default=None, max_length=32)
    clinvar_classification: PathogenicityLabel | None = None
    clinvar_review_status: str | None = None

    # ── Gemini explanation ────────────────────────────────────────────────────
    gemini_summary: str | None = None
    gemini_risk_level: str | None = None         # "low" | "moderate" | "high"
    top_tissues_affected: list[str] | None = Field(
        default=None, sa_column=Column(JSON)
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    analysis_job: "AnalysisJob" = Relationship(back_populates="variant_results")


from app.database.models.analysis_job import AnalysisJob  # noqa: E402