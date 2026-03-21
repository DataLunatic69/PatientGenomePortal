import logging

from app.database.models.analysis_job import JobStatus
from app.graph.state import AgentState, ScoredVariant

logger = logging.getLogger(__name__)

# Weight each signal's contribution to the final rank score
CLINVAR_WEIGHTS = {
    "pathogenic": 1.0,
    "likely_pathogenic": 0.8,
    "vus": 0.5,
    "likely_benign": 0.1,
    "benign": 0.0,
    "unknown": 0.3,
}

# Output types weighted by clinical relevance
EXPRESSION_WEIGHT = 0.40
SPLICING_WEIGHT = 0.30
CHROMATIN_WEIGHT = 0.15
CLINVAR_WEIGHT = 0.15


def _max_abs_quantile(delta_scores: dict, output_type: str) -> float:
    """Get max absolute quantile score for a given output type."""
    tissue_scores = delta_scores.get(output_type, {})
    if not tissue_scores:
        return 0.0
    return max(abs(v) for v in tissue_scores.values())


def _compute_rank_score(variant: ScoredVariant) -> float:
    """
    Aggregate all signals into a single 0–1 rank score.
    Higher = more likely to be clinically significant.
    """
    # 1. Expression signal (RNA_SEQ quantile, 0–1)
    expression_signal = min(
        _max_abs_quantile(variant.delta_scores, "RNA_SEQ"), 1.0
    )

    # 2. Splicing signal — normalize to 0–1 (empirical max ~6)
    splicing_signal = min(variant.splicing_score / 6.0, 1.0)

    # 3. Chromatin signal — average of ATAC + DNASE
    atac = _max_abs_quantile(variant.delta_scores, "ATAC")
    dnase = _max_abs_quantile(variant.delta_scores, "DNASE")
    chromatin_signal = min((atac + dnase) / 2.0, 1.0)

    # 4. ClinVar prior
    clinvar_signal = 0.3  # default: no ClinVar data
    if variant.clinvar and variant.clinvar.classification:
        clinvar_signal = CLINVAR_WEIGHTS.get(variant.clinvar.classification, 0.3)

    rank_score = (
        EXPRESSION_WEIGHT * expression_signal
        + SPLICING_WEIGHT * splicing_signal
        + CHROMATIN_WEIGHT * chromatin_signal
        + CLINVAR_WEIGHT * clinvar_signal
    )

    return round(rank_score, 4)


def rank_variants(state: AgentState) -> AgentState:
    """
    Node 4: Compute a composite rank score for each scored variant
    and sort descending (most concerning first).
    """
    logger.info(
        "rank_variants: starting",
        extra={"job_id": str(state.job_id), "count": len(state.scored_variants)},
    )
    state.current_step = JobStatus.RANKING
    state.progress_pct = 78

    if state.error or not state.scored_variants:
        return state

    for variant in state.scored_variants:
        variant.rank_score = _compute_rank_score(variant)

    ranked = sorted(state.scored_variants, key=lambda v: v.rank_score, reverse=True)

    for i, variant in enumerate(ranked):
        variant.rank_position = i + 1

    state.ranked_variants = ranked
    state.progress_pct = 82

    logger.info(
        "rank_variants: complete",
        extra={
            "job_id": str(state.job_id),
            "top_score": ranked[0].rank_score if ranked else 0,
        },
    )
    return state