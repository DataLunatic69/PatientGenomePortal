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
        job = await session.get(AnalysisJob, job_id_uuid)
        if not job:
            logger.error("job.not_found", job_id=job_id)
            return
        job.started_at = datetime.utcnow()
        job.status = JobStatus.PARSING
        job.current_step = JobStatus.PARSING.value
        job.progress_pct = 5
        await session.commit()

        try:
            start_graph_time = datetime.utcnow()
            final_state = await run_analysis(
                job_id=job_id_uuid,
                dna_file_id=dna_file_id_uuid,
                storage_path=storage_path,
                file_source=file_source,
            )
            graph_duration = (datetime.utcnow() - start_graph_time).total_seconds()
            logger.info("analysis.graph_complete", job_id=job_id, duration_seconds=graph_duration)

            # final_state is a dict returned by LangGraph (dataclass → dict at ainvoke boundary)
            pipeline_error: str | None = final_state.get("error")
            ranked_variants = final_state.get("ranked_variants") or []
            raw_snvs = final_state.get("raw_snvs") or []
            gemini_report: str = final_state.get("gemini_report") or ""
            progress_pct: int = final_state.get("progress_pct") or 100

            start_db_time = datetime.utcnow()

            # Persist variant results
            for v in ranked_variants:
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
                dna_file.parsed_at = datetime.utcnow()
                dna_file.total_variants_parsed = len(raw_snvs)

            # Update job status — always set explicitly, never derive from a string
            job = await session.get(AnalysisJob, job_id_uuid)
            if job:
                if pipeline_error:
                    job.status = JobStatus.FAILED
                    job.current_step = JobStatus.FAILED.value
                    job.error_message = pipeline_error
                else:
                    job.status = JobStatus.COMPLETED
                    job.current_step = JobStatus.COMPLETED.value
                    job.error_message = None
                job.progress_pct = progress_pct
                job.completed_at = datetime.utcnow()
                job.graph_state = {
                    "ranked_count": len(ranked_variants),
                    "gemini_report": gemini_report,
                }

            await session.commit()
            db_duration = (datetime.utcnow() - start_db_time).total_seconds()
            logger.info(
                "analysis.complete",
                job_id=job_id,
                ranked_variants=len(ranked_variants),
                has_error=bool(pipeline_error),
                db_duration_seconds=db_duration,
                total_duration_seconds=graph_duration + db_duration,
            )

        except Exception as exc:
            logger.exception("analysis.failed", job_id=job_id)
            job = await session.get(AnalysisJob, job_id_uuid)
            if job:
                job.status = JobStatus.FAILED
                job.current_step = JobStatus.FAILED.value
                job.error_message = str(exc)
                job.completed_at = datetime.utcnow()
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
