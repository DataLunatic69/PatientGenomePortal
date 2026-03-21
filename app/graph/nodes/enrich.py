import logging
import time

import httpx

from app.config import settings
from app.database.models.analysis_job import JobStatus
from app.graph.state import SNV, AgentState, ClinVarRecord

logger = logging.getLogger(__name__)

NCBI_EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CLINVAR_SEARCH_URL = f"{NCBI_EUTILS_BASE}/esearch.fcgi"
CLINVAR_SUMMARY_URL = f"{NCBI_EUTILS_BASE}/esummary.fcgi"

# Classifications we keep for scoring — benign variants are skipped
KEEP_CLASSIFICATIONS = {
    "Pathogenic",
    "Likely pathogenic",
    "Pathogenic/Likely pathogenic",
    "Uncertain significance",
    "Conflicting interpretations of pathogenicity",
}

# Map NCBI strings to our PathogenicityLabel values
CLASSIFICATION_MAP = {
    "Pathogenic": "pathogenic",
    "Likely pathogenic": "likely_pathogenic",
    "Pathogenic/Likely pathogenic": "likely_pathogenic",
    "Uncertain significance": "vus",
    "Conflicting interpretations of pathogenicity": "vus",
    "Likely benign": "likely_benign",
    "Benign": "benign",
    "Benign/Likely benign": "benign",
}


def _fetch_clinvar_for_rsid(rsid: str, client: httpx.Client) -> ClinVarRecord | None:
    """Query NCBI ClinVar for a single rsID."""
    if not rsid or not rsid.startswith("rs"):
        return None

    try:
        # Search ClinVar for the rsID
        search_resp = client.get(
            CLINVAR_SEARCH_URL,
            params={
                "db": "clinvar",
                "term": f"{rsid}[rs]",
                "retmode": "json",
                "retmax": 1,
            },
            timeout=10.0,
        )
        search_resp.raise_for_status()
        search_data = search_resp.json()

        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return None

        clinvar_id = id_list[0]

        # Fetch summary for the ClinVar record
        summary_resp = client.get(
            CLINVAR_SUMMARY_URL,
            params={
                "db": "clinvar",
                "id": clinvar_id,
                "retmode": "json",
            },
            timeout=10.0,
        )
        summary_resp.raise_for_status()
        summary_data = summary_resp.json()

        result = summary_data.get("result", {}).get(clinvar_id, {})
        clinical_sig = result.get("clinical_significance", {})
        raw_classification = clinical_sig.get("description", "")
        review_status = clinical_sig.get("review_status", "")

        return ClinVarRecord(
            clinvar_id=clinvar_id,
            classification=CLASSIFICATION_MAP.get(raw_classification, "unknown"),
            review_status=review_status,
        )

    except Exception as exc:
        logger.debug(f"ClinVar lookup failed for {rsid}: {exc}")
        return None


def enrich_clinvar(state: AgentState) -> AgentState:
    """
    Node 2: Look up each SNV in ClinVar.
    - Attaches ClinVar record where available.
    - Filters down to variants worth scoring:
      pathogenic / likely pathogenic / VUS + any without a ClinVar record.
    - Caps at settings.max_variants_to_score to keep scoring time reasonable.
    """
    logger.info(
        "enrich_clinvar: starting",
        extra={"job_id": str(state.job_id), "snv_count": len(state.raw_snvs)},
    )
    state.current_step = JobStatus.ENRICHING
    state.progress_pct = 20

    if state.error:
        return state

    clinvar_records: dict[str, ClinVarRecord] = {}

    with httpx.Client() as client:
        for i, snv in enumerate(state.raw_snvs):
            if snv.variant_id and snv.variant_id.startswith("rs"):
                record = _fetch_clinvar_for_rsid(snv.variant_id, client)
                if record:
                    clinvar_records[snv.variant_id] = record
                # Respect NCBI rate limit: 3 requests/second without API key
                time.sleep(0.34)

            # Update progress incrementally
            if i % 50 == 0:
                pct = 20 + int((i / max(len(state.raw_snvs), 1)) * 15)
                state.progress_pct = min(pct, 35)

    # Filter: keep pathogenic / VUS / no clinvar record (unknown = keep)
    filtered: list[SNV] = []
    for snv in state.raw_snvs:
        record = clinvar_records.get(snv.variant_id)
        if record is None:
            # No ClinVar data — include, AlphaGenome will score it
            filtered.append(snv)
        elif record.classification in ("pathogenic", "likely_pathogenic", "vus"):
            filtered.append(snv)
        # Skip confirmed benign / likely benign

    # Cap before scoring
    filtered = filtered[: settings.max_variants_to_score]

    # Attach ClinVar records back to SNVs via a lookup we pass through state
    # We store them in a way the score node can access
    for snv in filtered:
        record = clinvar_records.get(snv.variant_id)
        snv.__dict__["_clinvar"] = record  # temp attachment

    state.filtered_snvs = filtered
    state.progress_pct = 35

    logger.info(
        "enrich_clinvar: complete",
        extra={
            "job_id": str(state.job_id),
            "raw": len(state.raw_snvs),
            "filtered": len(filtered),
            "clinvar_hits": len(clinvar_records),
        },
    )
    return state