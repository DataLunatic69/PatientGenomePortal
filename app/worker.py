import httpx
from arq.connections import create_pool
from arq.worker import Worker
from arq.connections import RedisSettings
from urllib.parse import urlparse

from app.config import settings
from app.database.session import AsyncSessionLocal
from app.database.models.analysis_job import AnalysisJob, JobStatus
from app.database.models.dna_file import DnaFile
from app.database.models.variant_result import VariantResult
from app.graph.pipeline import run_analysis
from datetime import datetime, timezone
import structlog

logger = structlog.get_logger()

# Parse standard Redis URL to ARQ RedisSettings
parsed_redis_url = urlparse(settings.redis_url)
REDIS_SETTINGS = RedisSettings(
    host=parsed_redis_url.hostname or "localhost",
    port=parsed_redis_url.port or 6379,
    password=parsed_redis_url.password,
    database=int((parsed_redis_url.path or "/0").lstrip("/")),
    ssl=parsed_redis_url.scheme == "rediss",
)

async def analysis_worker_task(
    ctx: dict,
    job_id: str,
    dna_file_id: str,
    storage_path: str,
    file_source: str,
) -> None:
    """ARQ Worker: run LangGraph pipeline and persist results."""
    from uuid import UUID
    job_id_uuid = UUID(job_id)
    dna_file_id_uuid = UUID(dna_file_id)

    async with AsyncSessionLocal() as session:
        # Mark job as started
        job = await session.get(AnalysisJob, job_id_uuid)
        if not job:
            logger.error("job.not_found", job_id=job_id)
            return
        job.started_at = datetime.now(timezone.utc)
        job.status = JobStatus.PARSING
        await session.commit()

        try:
            final_state = await run_analysis(
                job_id=job_id_uuid,
                dna_file_id=dna_file_id_uuid,
                storage_path=storage_path,
                file_source=file_source,
            )

            # Persist variant results
            for v in final_state.ranked_variants:
                result = VariantResult(
                    analysis_job_id=job_id_uuid,
                    chromosome=v.snv.chromosome,
                    position=v.snv.position,
                    reference_bases=v.snv.reference_bases,
                    alternate_bases=v.snv.alternate_bases,
                    gene_name=v.snv.gene_name,
                    gene_id=v.snv.gene_id,
                    delta_scores=v.delta_scores,
                    splicing_score=v.splicing_score,
                    rank_score=v.rank_score,
                    rank_position=v.rank_position,
                    clinvar_id=v.clinvar.clinvar_id if v.clinvar else None,
                    clinvar_classification=v.clinvar.classification if v.clinvar else None,
                    clinvar_review_status=v.clinvar.review_status if v.clinvar else None,
                    gemini_summary=v.gemini_summary,
                    gemini_risk_level=v.gemini_risk_level,
                    top_tissues_affected=v.top_tissues_affected,
                )
                session.add(result)

            # Update dna_file parsed metadata
            dna_file = await session.get(DnaFile, dna_file_id_uuid)
            if dna_file:
                dna_file.parsed_at = datetime.now(timezone.utc)
                dna_file.total_variants_parsed = len(final_state.raw_snvs)

            # Update job to completed or failed
            job = await session.get(AnalysisJob, job_id_uuid)
            if job:
                job.status = final_state.current_step
                job.progress_pct = final_state.progress_pct
                job.error_message = final_state.error
                job.completed_at = datetime.now(timezone.utc)
                job.graph_state = {"ranked_count": len(final_state.ranked_variants), "gemini_report": final_state.gemini_report}

            await session.commit()
            logger.info("analysis.complete", job_id=job_id)

        except Exception as exc:
            logger.exception("analysis.failed", job_id=job_id)
            job = await session.get(AnalysisJob, job_id_uuid)
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(exc)
                job.completed_at = datetime.now(timezone.utc)
            await session.commit()
            raise


class WorkerSettings:
    """Config for ARQ worker."""
    functions = [analysis_worker_task]
    redis_settings = REDIS_SETTINGS
    
    async def on_startup(ctx: dict) -> None:
        logger.info("worker.started")

    async def on_shutdown(ctx: dict) -> None:
        logger.info("worker.shutdown")
