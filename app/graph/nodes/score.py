import logging

import pandas as pd
from alphagenome.data import genome
from alphagenome.models import dna_client, variant_scorers

from app.config import settings
from app.database.models.analysis_job import JobStatus
from app.graph.state import AgentState, ClinVarRecord, ScoredVariant

logger = logging.getLogger(__name__)

# Tissue ontologies we always score against — covers the most common disease genes
DEFAULT_ONTOLOGY_TERMS = [
    "UBERON:0000310",  # breast
    "UBERON:0000992",  # ovary
    "UBERON:0002107",  # liver
    "UBERON:0002048",  # lung
    "UBERON:0002106",  # spleen
    "UBERON:0001155",  # colon
    "UBERON:0000955",  # brain
    "CL:0000084",      # T-cell
    "CL:0000236",      # B cell
]

SEQUENCE_LENGTH_MAP = {
    "1MB": dna_client.SUPPORTED_SEQUENCE_LENGTHS["SEQUENCE_LENGTH_1MB"],
    "500KB": dna_client.SUPPORTED_SEQUENCE_LENGTHS["SEQUENCE_LENGTH_500KB"],
    "100KB": dna_client.SUPPORTED_SEQUENCE_LENGTHS["SEQUENCE_LENGTH_100KB"],
}


def _compute_splicing_score(df: pd.DataFrame) -> float:
    """
    Merged splicing score as described in the AlphaGenome paper:
    max(splice_sites) + max(splice_site_usage) + max(splice_junctions) / 5
    """
    def max_score(output_type: str) -> float:
        subset = df[df["output_type"] == output_type]["raw_score"]
        return float(subset.abs().max()) if not subset.empty else 0.0

    return (
        max_score("SPLICE_SITES")
        + max_score("SPLICE_SITE_USAGE")
        + max_score("SPLICE_JUNCTIONS") / 5.0
    )


def _extract_top_tissues(df: pd.DataFrame, top_n: int = 5) -> list[str]:
    """Return top N tissue names by absolute quantile score."""
    rna_df = df[df["output_type"] == "RNA_SEQ"].copy()
    if rna_df.empty:
        return []
    rna_df["abs_q"] = rna_df["quantile_score"].abs()
    top = (
        rna_df.sort_values("abs_q", ascending=False)
        .drop_duplicates("biosample_name")
        .head(top_n)["biosample_name"]
        .tolist()
    )
    return [t for t in top if isinstance(t, str)]


def _build_delta_scores_summary(df: pd.DataFrame) -> dict:
    """
    Compact JSON-friendly summary of delta scores per output type.
    Stores top 5 tissue hits per output type with their quantile scores.
    """
    summary: dict = {}
    for output_type in df["output_type"].unique():
        subset = df[df["output_type"] == output_type].copy()
        subset["abs_q"] = subset["quantile_score"].abs()
        top = (
            subset.sort_values("abs_q", ascending=False)
            .drop_duplicates("biosample_name")
            .head(5)
        )
        summary[output_type] = {
            row["biosample_name"]: round(float(row["quantile_score"]), 4)
            for _, row in top.iterrows()
            if pd.notna(row.get("biosample_name"))
        }
    return summary


def score_variants(state: AgentState) -> AgentState:
    """
    Node 3: Score each filtered variant with AlphaGenome.
    Uses score_variant() (fast, scalar) for all variants.
    Computes splicing score, delta score summary, and top tissues.
    """
    logger.info(
        "score_variants: starting",
        extra={"job_id": str(state.job_id), "count": len(state.filtered_snvs)},
    )
    state.current_step = JobStatus.SCORING
    state.progress_pct = 35

    if state.error or not state.filtered_snvs:
        return state

    dna_model = dna_client.create(settings.alphagenome_api_key)
    seq_length = SEQUENCE_LENGTH_MAP.get(settings.sequence_length,
                                          SEQUENCE_LENGTH_MAP["1MB"])

    # Use recommended scorers
    scorers = list(variant_scorers.RECOMMENDED_VARIANT_SCORERS.values())

    scored: list[ScoredVariant] = []
    total = len(state.filtered_snvs)

    for i, snv in enumerate(state.filtered_snvs):
        try:
            variant = genome.Variant(
                chromosome=snv.chromosome,
                position=snv.position,
                reference_bases=snv.reference_bases,
                alternate_bases=snv.alternate_bases,
                name=snv.variant_id or f"{snv.chromosome}:{snv.position}",
            )
            interval = variant.reference_interval.resize(seq_length)

            raw_scores = dna_model.score_variant(
                interval=interval,
                variant=variant,
                variant_scorers=scorers,
                organism=dna_client.Organism.HOMO_SAPIENS,
            )

            df = variant_scorers.tidy_scores([raw_scores])

            clinvar: ClinVarRecord | None = snv.__dict__.pop("_clinvar", None)

            scored.append(
                ScoredVariant(
                    snv=snv,
                    clinvar=clinvar,
                    delta_scores=_build_delta_scores_summary(df),
                    splicing_score=_compute_splicing_score(df),
                    top_tissues_affected=_extract_top_tissues(df),
                )
            )

        except Exception as exc:
            logger.warning(
                f"score_variants: failed for {snv.variant_id} — {exc}"
            )
            # Include with empty scores so it still appears in results
            scored.append(ScoredVariant(snv=snv))

        # Update progress: 35 → 75 across all variants
        state.progress_pct = 35 + int(((i + 1) / total) * 40)

    state.scored_variants = scored
    state.progress_pct = 75

    logger.info(
        "score_variants: complete",
        extra={"job_id": str(state.job_id), "scored": len(scored)},
    )
    return state