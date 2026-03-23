import io
import logging

import pandas as pd
from supabase import create_client

from app.config import settings
from app.database.models.analysis_job import JobStatus
from app.graph.state import SNV, AgentState

logger = logging.getLogger(__name__)


def _download_file(storage_path: str) -> bytes:
    """Download raw DNA file from Supabase storage."""
    client = create_client(settings.supabase_url, settings.supabase_service_key)
    response = client.storage.from_(settings.supabase_bucket_name).download(
        storage_path
    )
    return response


def _split_line(line: str) -> list[str]:
    """
    Split a data line by commas (CSV) or whitespace (TSV/space-delimited).
    Strips surrounding whitespace and quotes from each field.
    """
    if "," in line:
        return [f.strip().strip('"').strip("'") for f in line.split(",")]
    return line.split()


def _parse_23andme(content: str) -> list[SNV]:
    """
    Parse 23andMe raw data format.
    Supports both whitespace-delimited (standard export) and
    comma-separated (CSV export) with columns:
        rsid  chromosome  position  genotype
    Lines starting with # are comments; header lines are skipped automatically
    because int(position) will fail on the literal string "position".
    """
    snvs: list[SNV] = []
    lines = [l for l in content.splitlines() if not l.startswith("#") and l.strip()]

    for line in lines:
        parts = _split_line(line)
        if len(parts) < 4:
            continue

        rsid, chrom, pos_str, genotype = parts[0], parts[1], parts[2], parts[3]

        if not chrom.startswith("chr"):
            chrom = f"chr{chrom}"

        try:
            position = int(pos_str)
        except ValueError:
            continue  # skip header or non-numeric rows

        ref = genotype[0] if len(genotype) > 0 else "N"
        alt = genotype[1] if len(genotype) > 1 else ref

        snvs.append(
            SNV(
                chromosome=chrom,
                position=position,
                reference_bases=ref,
                alternate_bases=alt,
                variant_id=rsid,
            )
        )

    return snvs


def _parse_vcf(content: str) -> list[SNV]:
    """
    Parse standard VCF format (tab or space delimited).
    Columns: CHROM POS ID REF ALT QUAL FILTER INFO ...
    Lines starting with # are comments / header.
    """
    snvs: list[SNV] = []
    lines = [l for l in content.splitlines() if not l.startswith("#") and l.strip()]

    for line in lines:
        parts = _split_line(line)
        if len(parts) < 5:
            continue

        chrom, pos_str, variant_id, ref, alt_field = (
            parts[0], parts[1], parts[2], parts[3], parts[4],
        )

        if not chrom.startswith("chr"):
            chrom = f"chr{chrom}"

        try:
            position = int(pos_str)
        except ValueError:
            continue

        alt = alt_field.split(",")[0]

        snvs.append(
            SNV(
                chromosome=chrom,
                position=position,
                reference_bases=ref,
                alternate_bases=alt,
                variant_id=variant_id if variant_id != "." else "",
            )
        )

    return snvs


def parse_dna_file(state: AgentState) -> AgentState:
    import time
    start_time = time.perf_counter()
    """
    Node 1: Download DNA file from Supabase and parse into SNV list.
    Handles 23andMe and VCF formats.
    """
    logger.info(
        "parse_dna_file: starting",
        extra={"job_id": str(state.job_id), "source": state.file_source},
    )
    state.current_step = JobStatus.PARSING
    state.progress_pct = 5

    try:
        raw_bytes = _download_file(state.storage_path)
        content = raw_bytes.decode("utf-8", errors="replace")

        match state.file_source:
            case "23andme" | "ancestry":
                snvs = _parse_23andme(content)
            case "vcf":
                snvs = _parse_vcf(content)
            case _:
                # Try VCF first, fall back to 23andMe format
                try:
                    snvs = _parse_vcf(content)
                    if not snvs:
                        snvs = _parse_23andme(content)
                except Exception:
                    snvs = _parse_23andme(content)

        state.raw_snvs = snvs
        state.progress_pct = 15
        logger.info(
            "parse_dna_file: complete",
            extra={"job_id": str(state.job_id), "total_snvs": len(snvs), "duration_seconds": time.perf_counter() - start_time},
        )

    except Exception as exc:
        logger.exception("parse_dna_file: failed")
        state.error = f"Failed to parse DNA file: {exc}"

    return state