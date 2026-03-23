import asyncio
import logging
import time

import httpx

from app.config import settings
from app.database.models.analysis_job import JobStatus
from app.graph.state import SNV, AgentState, ClinVarRecord

logger = logging.getLogger(__name__)

# Maximum number of raw SNVs to enrich — prevents multi-hour runs on large 23andMe files
MAX_SNVS_TO_ENRICH = 5000

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

# Classifications we score — benign variants are skipped; unknown/unrecognised are kept
SCORE_CLASSIFICATIONS = {"pathogenic", "likely_pathogenic", "vus", "unknown"}
# Classifications definitively considered benign — these are the only ones we drop
SKIP_CLASSIFICATIONS = {"benign", "likely_benign"}


async def _fetch_clinvar_for_rsid_async(rsid: str, client: httpx.AsyncClient) -> tuple[ClinVarRecord | None, str | None]:
    """Query myvariant.info for ClinVar and gene symbol."""
    if not rsid or not rsid.startswith("rs"):
        return None, None

    try:
        resp = await client.get(
            f"https://myvariant.info/v1/query",
            params={"q": rsid, "fields": "clinvar,dbsnp.gene", "size": 1},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        
        if not data.get("hits"):
            return None, None
            
        hit = data["hits"][0]
        
        # Extract gene symbol safely
        gene_symbol = None
        dbsnp = hit.get("dbsnp", {})
        if isinstance(dbsnp, dict):
            gene = dbsnp.get("gene")
            if isinstance(gene, dict):
                gene_symbol = gene.get("symbol")
            elif isinstance(gene, list) and len(gene) > 0:
                gene_symbol = gene[0].get("symbol")
                
        # Extract clinvar safely
        clinvar_data = hit.get("clinvar")
        if not clinvar_data:
            return None, gene_symbol
            
        rcv = clinvar_data.get("rcv", [])
        if not rcv:
            return None, gene_symbol
            
        # rcv can be dict or list
        first_rcv = rcv[0] if isinstance(rcv, list) else rcv
        raw_classification = first_rcv.get("clinical_significance", "")
        review_status = first_rcv.get("review_status", "")
        clinvar_id = first_rcv.get("accession", "")
        
        # lowercase map
        raw_mapped = CLASSIFICATION_MAP.get(raw_classification, "unknown")
        # try to map case-insensitively if not found
        if raw_mapped == "unknown" and raw_classification:
            for k, v in CLASSIFICATION_MAP.items():
                if k.lower() == raw_classification.lower():
                    raw_mapped = v
                    break

        record = ClinVarRecord(
            clinvar_id=clinvar_id,
            classification=raw_mapped,
            review_status=review_status,
        )
        return record, gene_symbol

    except Exception as exc:
        logger.debug(f"MyVariant lookup failed for {rsid}: {exc}")
        return None, None

async def _process_batch(batch, client, clinvar_records):
    # Process a batch concurrently
    tasks = []
    for snv in batch:
        if snv.variant_id and snv.variant_id.startswith("rs"):
            tasks.append(_fetch_clinvar_for_rsid_async(snv.variant_id, client))
        else:
            async def null_result(): return None, None
            tasks.append(null_result())

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, snv in enumerate(batch):
        res = results[i]
        if isinstance(res, Exception):
            logger.error(f"Failed to fetch {snv.variant_id}: {res}")
            continue

        record, gene = res
        if record:
            clinvar_records[snv.variant_id] = record
        if gene:
            snv.gene_name = gene


def enrich_clinvar(state: AgentState) -> AgentState:
    import time
    start_time = time.perf_counter()
    """
    Node 2: Look up each SNV in ClinVar via MyVariant.info.
    - Attaches ClinVar record where available.
    - Filters down to variants worth scoring:
        pathogenic / likely_pathogenic / vus / unknown + any without a ClinVar record.
    - Confirmed benign / likely_benign variants are the only ones dropped.
    - Caps enrichment at MAX_SNVS_TO_ENRICH to avoid multi-hour runs on large files.
    - Caps scoring input at settings.max_variants_to_score.
    """
    logger.info(
        "enrich_clinvar: starting",
        extra={"job_id": str(state.job_id), "snv_count": len(state.raw_snvs)},
    )
    state.current_step = JobStatus.ENRICHING.value
    state.progress_pct = 20

    if state.error:
        return state

    # Pre-cap: for very large files (e.g., 23andMe with 600k variants) process only
    # the first MAX_SNVS_TO_ENRICH to avoid spending hours on ClinVar lookups.
    snvs_to_enrich = state.raw_snvs[:MAX_SNVS_TO_ENRICH]
    if len(state.raw_snvs) > MAX_SNVS_TO_ENRICH:
        logger.warning(
            "enrich_clinvar: capping enrichment",
            extra={"job_id": str(state.job_id), "total": len(state.raw_snvs), "cap": MAX_SNVS_TO_ENRICH},
        )

    clinvar_records: dict[str, ClinVarRecord] = {}

    async def _run_enrichment():
        async with httpx.AsyncClient() as client:
            batch_size = 50
            for i in range(0, len(snvs_to_enrich), batch_size):
                batch = snvs_to_enrich[i:i + batch_size]
                await _process_batch(batch, client, clinvar_records)

                pct = 20 + int(((i + len(batch)) / max(len(snvs_to_enrich), 1)) * 15)
                state.progress_pct = min(pct, 35)
                await asyncio.sleep(0.01)

    asyncio.run(_run_enrichment())

    # Filter: keep everything EXCEPT definitively benign variants.
    # - No ClinVar record → include (AlphaGenome will score it)
    # - pathogenic / likely_pathogenic / vus / unknown → include
    # - benign / likely_benign → drop
    filtered: list[SNV] = []
    benign_dropped = 0
    for snv in snvs_to_enrich:
        record = clinvar_records.get(snv.variant_id)
        if record is None or record.classification not in SKIP_CLASSIFICATIONS:
            filtered.append(snv)
        else:
            benign_dropped += 1

    # Cap before scoring
    filtered = filtered[: settings.max_variants_to_score]

    # Attach ClinVar records to SNVs so the score node can access them
    for snv in filtered:
        record = clinvar_records.get(snv.variant_id)
        snv.__dict__["_clinvar"] = record  # temp attachment, popped in score node

    state.filtered_snvs = filtered
    state.progress_pct = 35

    logger.info(
        "enrich_clinvar: complete",
        extra={
            "job_id": str(state.job_id),
            "raw": len(state.raw_snvs),
            "enriched": len(snvs_to_enrich),
            "filtered": len(filtered),
            "benign_dropped": benign_dropped,
            "clinvar_hits": len(clinvar_records),
            "duration_seconds": time.perf_counter() - start_time,
        },
    )
    return state
