import structlog
import pandas as pd
from alphagenome.data import genome
from alphagenome.models import dna_client, variant_scorers

from app.config import settings

logger = structlog.get_logger()

# Sequence length used for all scoring — 1MB gives best predictions
SEQUENCE_LENGTH = dna_client.SUPPORTED_SEQUENCE_LENGTHS["SEQUENCE_LENGTH_1MB"]

# Default tissue ontologies scored for every variant
DEFAULT_ONTOLOGIES = [
    "UBERON:0000310",  # breast
    "UBERON:0000992",  # ovary
    "UBERON:0002107",  # liver
    "UBERON:0002048",  # lung
    "UBERON:0001155",  # colon
    "UBERON:0000955",  # brain
    "CL:0000084",      # T-cell
    "CL:0000236",      # B cell
]


def _get_client() -> dna_client.DnaClient:
    return dna_client.create(settings.alphagenome_api_key)


def _get_scorers() -> list:
    return list(variant_scorers.RECOMMENDED_VARIANT_SCORERS.values())


# ── Scoring ───────────────────────────────────────────────────────────────────

def score_variant(
    chromosome: str,
    position: int,
    reference_bases: str,
    alternate_bases: str,
    variant_id: str = "",
) -> pd.DataFrame:
    """
    Score a single variant across all recommended scorers.
    Returns a tidy DataFrame with columns:
      output_type, biosample_name, ontology_curie,
      raw_score, quantile_score, ...
    """
    variant = genome.Variant(
        chromosome=chromosome,
        position=position,
        reference_bases=reference_bases,
        alternate_bases=alternate_bases,
        name=variant_id or f"{chromosome}:{position}",
    )
    interval = variant.reference_interval.resize(SEQUENCE_LENGTH)

    logger.info("Calling AlphaGenome score_variant", chromosome=chromosome, position=position, ref=reference_bases, alt=alternate_bases)
    raw = _get_client().score_variant(
        interval=interval,
        variant=variant,
        variant_scorers=_get_scorers(),
        organism=dna_client.Organism.HOMO_SAPIENS,
    )
    return variant_scorers.tidy_scores([raw])


def predict_variant_tracks(
    chromosome: str,
    position: int,
    reference_bases: str,
    alternate_bases: str,
    ontology_terms: list[str] | None = None,
) -> tuple:
    """
    Call predict_variant() to get full REF/ALT track arrays.
    Used only for the top-ranked variants that need visualization.
    Returns (reference_output, alternate_output).
    """
    variant = genome.Variant(
        chromosome=chromosome,
        position=position,
        reference_bases=reference_bases,
        alternate_bases=alternate_bases,
    )
    interval = variant.reference_interval.resize(SEQUENCE_LENGTH)
    terms = ontology_terms or DEFAULT_ONTOLOGIES

    output = _get_client().predict_variant(
        interval=interval,
        variant=variant,
        requested_outputs={
            dna_client.OutputType.RNA_SEQ,
            dna_client.OutputType.ATAC,
            dna_client.OutputType.DNASE,
            dna_client.OutputType.CHIP_HISTONE,
            dna_client.OutputType.SPLICE_SITES,
            dna_client.OutputType.SPLICE_SITE_USAGE,
            dna_client.OutputType.SPLICE_JUNCTIONS,
        },
        ontology_terms=terms,
        organism=dna_client.Organism.HOMO_SAPIENS,
    )
    return output.reference, output.alternate


# ── Score extraction helpers ──────────────────────────────────────────────────

def compute_splicing_score(df: pd.DataFrame) -> float:
    """
    Merged splicing score (AlphaGenome paper formula):
    max(splice_sites) + max(splice_site_usage) + max(splice_junctions) / 5
    """
    def _max(output_type: str) -> float:
        s = df[df["output_type"] == output_type]["raw_score"]
        return float(s.abs().max()) if not s.empty else 0.0

    return _max("SPLICE_SITES") + _max("SPLICE_SITE_USAGE") + _max("SPLICE_JUNCTIONS") / 5.0


def extract_top_tissues(df: pd.DataFrame, top_n: int = 5) -> list[str]:
    """Top N tissue names by absolute RNA_SEQ quantile score."""
    rna = df[df["output_type"] == "RNA_SEQ"].copy()
    if rna.empty:
        return []
    rna["abs_q"] = rna["quantile_score"].abs()
    return (
        rna.sort_values("abs_q", ascending=False)
        .drop_duplicates("biosample_name")
        .head(top_n)["biosample_name"]
        .dropna()
        .tolist()
    )


def build_delta_scores_summary(df: pd.DataFrame) -> dict:
    """
    Compact per-output-type summary of top 5 tissue delta scores.
    Shape: { "RNA_SEQ": { "breast": 0.93, ... }, "ATAC": { ... }, ... }
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