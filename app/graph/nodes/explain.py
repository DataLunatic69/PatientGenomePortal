import json
import logging

import google.generativeai as genai

from app.config import settings
from app.database.models.analysis_job import JobStatus
from app.graph.state import AgentState, ScoredVariant

logger = logging.getLogger(__name__)

RISK_THRESHOLDS = {
    "high": 0.65,
    "moderate": 0.35,
}

VARIANT_PROMPT = """\
You are a genetic counselor explaining DNA variant results to a patient.
Be clear, compassionate, and avoid jargon. Use simple language a non-scientist can understand.

Here is the data for one genetic variant:

```json
{variant_json}
```

Write a 2-3 sentence plain-language explanation covering:
1. Which gene is affected and what it normally does (if known)
2. What this variant might mean for health (based on the scores and ClinVar classification)
3. What tissues or organs are most affected according to the model

Do NOT use phrases like "delta score", "quantile", "AlphaGenome", or other technical terms.
Do NOT give definitive medical diagnoses. Always recommend consulting a genetic counselor.
"""

REPORT_PROMPT = """\
You are a genetic counselor writing a summary report for a patient about their DNA analysis.
Write in plain, compassionate language. The patient has no biology background.

Here are their top {n} variants of concern, ranked by potential significance:

```json
{variants_json}
```

Write a patient report with these sections:
1. **Overview** (2-3 sentences): What this analysis found overall.
2. **Key findings** (bullet points): One bullet per variant, in plain English.
3. **What this means** (2-3 sentences): Practical guidance on next steps.
4. **Important note**: Always end by recommending they discuss results with a licensed genetic counselor or physician.

Keep the total report under 500 words. Do NOT use technical genomics terminology.
"""


def _variant_to_prompt_dict(v: ScoredVariant) -> dict:
    """Convert a ScoredVariant to a clean dict for the Gemini prompt."""
    return {
        "gene": v.snv.gene_name or "unknown gene",
        "variant": f"{v.snv.chromosome}:{v.snv.position} {v.snv.reference_bases}→{v.snv.alternate_bases}",
        "clinvar_classification": v.clinvar.classification if v.clinvar else "not in database",
        "top_tissues_affected": v.top_tissues_affected[:5],
        "splicing_disruption": v.splicing_score > 1.0,
        "expression_change": _expression_direction(v),
        "rank_score": v.rank_score,
        "risk_level": _risk_level(v.rank_score),
    }


def _expression_direction(v: ScoredVariant) -> str:
    rna_scores = v.delta_scores.get("RNA_SEQ", {})
    if not rna_scores:
        return "unknown"
    avg = sum(rna_scores.values()) / len(rna_scores)
    if avg > 0.1:
        return "increased"
    if avg < -0.1:
        return "decreased"
    return "minimal change"


def _risk_level(rank_score: float) -> str:
    if rank_score >= RISK_THRESHOLDS["high"]:
        return "high"
    if rank_score >= RISK_THRESHOLDS["moderate"]:
        return "moderate"
    return "low"


def explain_variants(state: AgentState) -> AgentState:
    """
    Node 5: Use Gemini to generate plain-language explanations for each
    top variant and a full patient report.
    """
    logger.info(
        "explain_variants: starting",
        extra={"job_id": str(state.job_id)},
    )
    state.current_step = JobStatus.EXPLAINING
    state.progress_pct = 85

    if state.error or not state.ranked_variants:
        return state

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-1.5-pro")

    # Explain top N variants individually
    top_variants = state.ranked_variants[: settings.max_variants_to_visualize]

    for i, variant in enumerate(top_variants):
        try:
            variant_dict = _variant_to_prompt_dict(variant)
            prompt = VARIANT_PROMPT.format(
                variant_json=json.dumps(variant_dict, indent=2)
            )
            response = model.generate_content(prompt)
            variant.gemini_summary = response.text.strip()
            variant.gemini_risk_level = _risk_level(variant.rank_score)

        except Exception as exc:
            logger.warning(f"explain_variants: Gemini failed for variant {i}: {exc}")
            variant.gemini_summary = (
                "Summary unavailable. Please consult a genetic counselor."
            )
            variant.gemini_risk_level = _risk_level(variant.rank_score)

        state.progress_pct = 85 + int(((i + 1) / len(top_variants)) * 10)

    # Generate full patient report
    try:
        variants_for_report = [_variant_to_prompt_dict(v) for v in top_variants]
        report_prompt = REPORT_PROMPT.format(
            n=len(top_variants),
            variants_json=json.dumps(variants_for_report, indent=2),
        )
        report_response = model.generate_content(report_prompt)
        state.gemini_report = report_response.text.strip()

    except Exception as exc:
        logger.warning(f"explain_variants: report generation failed: {exc}")
        state.gemini_report = (
            "Report generation failed. Please consult a genetic counselor "
            "to review your individual variant results."
        )

    state.ranked_variants = top_variants
    state.current_step = JobStatus.COMPLETED
    state.progress_pct = 100

    logger.info(
        "explain_variants: complete",
        extra={"job_id": str(state.job_id)},
    )
    return state