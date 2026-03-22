import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.api.schemas import ReportRead, VariantResultPage, VariantResultRead
from app.database.models.analysis_job import AnalysisJob, JobStatus
from app.database.models.variant_result import VariantResult
from app.database.session import get_db

logger = structlog.get_logger()

router = APIRouter()


@router.get("/{job_id}", response_model=VariantResultPage)
async def get_variants(
    job_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    risk_level: str | None = Query(default=None),   # "high" | "moderate" | "low"
    db: AsyncSession = Depends(get_db),
) -> VariantResultPage:
    """
    Paginated variant results for a completed analysis job.
    Optionally filter by Gemini risk level.
    Results are ordered by rank_position (most concerning first).
    """
    job = await db.get(AnalysisJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Job is not completed yet (status: {job.status})",
        )

    # Base query
    query = select(VariantResult).where(VariantResult.analysis_job_id == job_id)

    if risk_level:
        query = query.where(VariantResult.gemini_risk_level == risk_level)

    # Total count
    count_result = await db.exec(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.one()

    # Paginated results ordered by rank
    offset = (page - 1) * page_size
    result = await db.exec(
        query.order_by(VariantResult.rank_position).offset(offset).limit(page_size)
    )
    variants = result.all()

    return VariantResultPage(
        total=total,
        page=page,
        page_size=page_size,
        items=[VariantResultRead.model_validate(v) for v in variants],
    )


@router.get("/{job_id}/report", response_model=ReportRead)
async def get_report(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ReportRead:
    """
    Return the Gemini-generated patient report and risk summary counts
    for a completed analysis job.
    """
    job = await db.get(AnalysisJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Job not completed yet (status: {job.status})",
        )

    result = await db.exec(
        select(VariantResult)
        .where(VariantResult.analysis_job_id == job_id)
        .order_by(VariantResult.rank_position)
    )
    variants = result.all()

    high = sum(1 for v in variants if v.gemini_risk_level == "high")
    moderate = sum(1 for v in variants if v.gemini_risk_level == "moderate")
    low = sum(1 for v in variants if v.gemini_risk_level == "low")

    # Gemini report is stored on the first (top-ranked) variant's job state
    gemini_report = job.graph_state.get("gemini_report", "") if job.graph_state else ""

    return ReportRead(
        job_id=job_id,
        gemini_report=gemini_report,
        total_variants_analyzed=len(variants),
        high_risk_count=high,
        moderate_risk_count=moderate,
        low_risk_count=low,
    )


@router.get("/{job_id}/variant/{variant_id}/tracks")
async def get_variant_tracks(
    job_id: uuid.UUID,
    variant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Return the full delta_scores track data for a single variant.
    Used by the frontend to render the per-variant visualization charts.
    """
    variant = await db.get(VariantResult, variant_id)
    if not variant or variant.analysis_job_id != job_id:
        raise HTTPException(status_code=404, detail="Variant not found")

    return {
        "variant_id": str(variant_id),
        "chromosome": variant.chromosome,
        "position": variant.position,
        "gene_name": variant.gene_name,
        "delta_scores": variant.delta_scores or {},
        "splicing_score": variant.splicing_score,
        "top_tissues_affected": variant.top_tissues_affected or [],
    }