from dataclasses import dataclass, field
from uuid import UUID

from app.database.models.analysis_job import JobStatus


@dataclass
class SNV:
    """A single nucleotide variant parsed from a DNA file."""
    chromosome: str
    position: int
    reference_bases: str
    alternate_bases: str
    variant_id: str = ""
    gene_name: str | None = None
    gene_id: str | None = None


@dataclass
class ClinVarRecord:
    """ClinVar enrichment for a variant."""
    clinvar_id: str | None = None
    classification: str | None = None   # pathogenic / benign / vus etc.
    review_status: str | None = None


@dataclass
class ScoredVariant:
    """A variant after AlphaGenome scoring."""
    snv: SNV
    clinvar: ClinVarRecord | None = None
    delta_scores: dict = field(default_factory=dict)
    splicing_score: float = 0.0
    rank_score: float = 0.0
    rank_position: int = 0
    top_tissues_affected: list[str] = field(default_factory=list)
    gemini_summary: str | None = None
    gemini_risk_level: str | None = None  # "low" | "moderate" | "high"


@dataclass
class AgentState:
    """
    Full state that flows through every LangGraph node.
    Each node receives this, mutates it, and returns it.
    """
    # ── inputs set before graph runs ─────────────────────────────────────────
    job_id: UUID | None = None
    dna_file_id: UUID | None = None
    storage_path: str = ""             # Supabase storage path of uploaded file
    file_source: str = ""              # "23andme" | "vcf" | "ancestry" | "raw"

    # ── node outputs (populated as graph progresses) ──────────────────────────
    raw_snvs: list[SNV] = field(default_factory=list)
    filtered_snvs: list[SNV] = field(default_factory=list)   # after ClinVar filter
    scored_variants: list[ScoredVariant] = field(default_factory=list)
    ranked_variants: list[ScoredVariant] = field(default_factory=list)
    gemini_report: str = ""            # full patient-facing report

    # ── progress ──────────────────────────────────────────────────────────────
    current_step: JobStatus = JobStatus.PENDING
    progress_pct: int = 0
    error: str | None = None