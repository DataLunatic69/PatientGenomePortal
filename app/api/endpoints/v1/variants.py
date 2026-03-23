import uuid
import json

from google import genai
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.api.schemas import (
    ReportRead,
    VariantResultPage,
    VariantResultRead,
    ResultsChatRequest,
    ResultsChatResponse,
)
from app.config import settings
from app.database.models.analysis_job import AnalysisJob, JobStatus
from app.database.models.variant_result import VariantResult
from app.database.session import get_db
from app.services.gemini import generate_with_retry

logger = structlog.get_logger()

router = APIRouter()

CHAT_PROMPT = """\
You are a careful patient-facing genomic assistant.
Answer ONLY using the provided analysis context.
Keep answers concise and easy to understand.
If the context does not contain enough information, say so clearly.
Never provide diagnosis or treatment instructions.
Always recommend consulting a licensed genetic counselor or physician for clinical decisions.

Patient report:
{report}

Top variant findings:
{variants_json}

Conversation so far:
{history_json}

Patient question:
{question}
"""


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
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    # Paginated results ordered by rank
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(VariantResult.rank_position).offset(offset).limit(page_size)
    )
    variants = result.scalars().all()

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

    result = await db.execute(
        select(VariantResult)
        .where(VariantResult.analysis_job_id == job_id)
        .order_by(VariantResult.rank_position)
    )
    variants = result.scalars().all()

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


@router.post("/{job_id}/chat", response_model=ResultsChatResponse)
async def chat_about_results(
    job_id: uuid.UUID,
    payload: ResultsChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ResultsChatResponse:
    """Answer patient questions grounded in completed job results."""
    job = await db.get(AnalysisJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Job not completed yet (status: {job.status})",
        )

    result = await db.execute(
        select(VariantResult)
        .where(VariantResult.analysis_job_id == job_id)
        .order_by(VariantResult.rank_position)
        .limit(15)
    )
    top_variants = result.scalars().all()

    variants_payload = [
        {
            "rank": v.rank_position,
            "gene": v.gene_name,
            "variant": f"{v.chromosome}:{v.position} {v.reference_bases}>{v.alternate_bases}",
            "risk_level": v.gemini_risk_level,
            "clinvar": v.clinvar_classification,
            "summary": v.gemini_summary,
            "top_tissues": v.top_tissues_affected,
        }
        for v in top_variants
    ]

    report_text = ""
    if job.graph_state:
        report_text = str(job.graph_state.get("gemini_report", ""))

    history_payload = [
        {"role": msg.role, "content": msg.content}
        for msg in payload.history[-8:]
        if msg.content.strip()
    ]

    prompt = CHAT_PROMPT.format(
        report=report_text or "No report available.",
        variants_json=json.dumps(variants_payload, ensure_ascii=False, indent=2),
        history_json=json.dumps(history_payload, ensure_ascii=False, indent=2),
        question=payload.message.strip(),
    )

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        answer = generate_with_retry(client, prompt)
    except Exception as exc:
        logger.exception("variants.chat_failed", job_id=str(job_id), error=str(exc))
        raise HTTPException(status_code=502, detail="Failed to generate chat response")

    if not answer:
        answer = (
            "I couldn't generate an answer from the current analysis context. "
            "Please try rephrasing your question."
        )

    return ResultsChatResponse(answer=answer)