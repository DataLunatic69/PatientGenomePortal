import time

import httpx
import structlog

logger = structlog.get_logger()

NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
SEARCH_URL = f"{NCBI_BASE}/esearch.fcgi"
SUMMARY_URL = f"{NCBI_BASE}/esummary.fcgi"

# Variants with these classifications are worth scoring with AlphaGenome
SCOREABLE_CLASSIFICATIONS = {
    "pathogenic",
    "likely_pathogenic",
    "vus",
    "unknown",
}

CLASSIFICATION_MAP: dict[str, str] = {
    "Pathogenic": "pathogenic",
    "Likely pathogenic": "likely_pathogenic",
    "Pathogenic/Likely pathogenic": "likely_pathogenic",
    "Uncertain significance": "vus",
    "Conflicting interpretations of pathogenicity": "vus",
    "Likely benign": "likely_benign",
    "Benign": "benign",
    "Benign/Likely benign": "benign",
}


class ClinVarRecord:
    __slots__ = ("clinvar_id", "classification", "review_status")

    def __init__(
        self,
        clinvar_id: str | None,
        classification: str | None,
        review_status: str | None,
    ) -> None:
        self.clinvar_id = clinvar_id
        self.classification = classification
        self.review_status = review_status


def lookup_rsid(rsid: str, client: httpx.Client) -> ClinVarRecord | None:
    """
    Fetch ClinVar classification for a single rsID.
    Returns None if the rsID is not in ClinVar.
    """
    if not rsid or not rsid.startswith("rs"):
        return None

    try:
        search = client.get(
            SEARCH_URL,
            params={"db": "clinvar", "term": f"{rsid}[rs]", "retmode": "json", "retmax": 1},
            timeout=10.0,
        )
        search.raise_for_status()
        id_list = search.json().get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return None

        clinvar_id = id_list[0]

        summary = client.get(
            SUMMARY_URL,
            params={"db": "clinvar", "id": clinvar_id, "retmode": "json"},
            timeout=10.0,
        )
        summary.raise_for_status()
        rec = summary.json().get("result", {}).get(clinvar_id, {})
        sig = rec.get("clinical_significance", {})
        raw = sig.get("description", "")

        return ClinVarRecord(
            clinvar_id=clinvar_id,
            classification=CLASSIFICATION_MAP.get(raw, "unknown"),
            review_status=sig.get("review_status"),
        )

    except Exception as exc:
        logger.debug("clinvar.lookup_failed", rsid=rsid, error=str(exc))
        return None


def batch_lookup(
    rsids: list[str],
    rate_limit_delay: float = 0.34,   # 3 req/s without NCBI API key
) -> dict[str, ClinVarRecord]:
    """
    Look up a list of rsIDs against ClinVar.
    Returns a dict of rsid → ClinVarRecord for hits only.
    """
    results: dict[str, ClinVarRecord] = {}

    with httpx.Client() as client:
        for rsid in rsids:
            record = lookup_rsid(rsid, client)
            if record:
                results[rsid] = record
            time.sleep(rate_limit_delay)

    logger.info(
        "clinvar.batch_complete",
        total=len(rsids),
        hits=len(results),
    )
    return results


def is_scoreable(record: ClinVarRecord | None) -> bool:
    """
    Return True if this variant should be sent to AlphaGenome for scoring.
    Confirmed benign variants are skipped to save API calls.
    """
    if record is None:
        return True   # no ClinVar data → unknown → score it
    return record.classification in SCOREABLE_CLASSIFICATIONS