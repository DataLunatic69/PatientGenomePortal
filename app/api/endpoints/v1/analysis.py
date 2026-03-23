import asyncio
import json
import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.schemas import AnalysisJobRead, JobStatusUpdate
from app.database.models.analysis_job import AnalysisJob, JobStatus
from app.database.session import get_db

logger = structlog.get_logger()

router = APIRouter()

TERMINAL_STATUSES = {JobStatus.COMPLETED, JobStatus.FAILED}
SSE_POLL_INTERVAL = 1.5   # seconds between DB polls


@router.get("/{job_id}", response_model=AnalysisJobRead)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AnalysisJobRead:
    """Get current status of an analysis job."""
    job = await db.get(AnalysisJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return AnalysisJobRead.model_validate(job)


@router.get("/{job_id}/stream")
async def stream_job_status(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    SSE endpoint — streams job progress events until the job reaches
    a terminal state (completed or failed).
    The Next.js frontend connects here via EventSource.
    """
    async def event_generator():
        last_pct = -1

        while True:
            # Single expunge+get to force a fresh DB read each tick
            db.expire_all()
            job = await db.get(AnalysisJob, job_id)

            if not job:
                yield _sse_event({"error": "Job not found"})
                break

            if job.progress_pct != last_pct or job.status in TERMINAL_STATUSES:
                last_pct = job.progress_pct
                payload = JobStatusUpdate(
                    job_id=job_id,
                    status=job.status,
                    current_step=job.current_step,
                    progress_pct=job.progress_pct,
                    error_message=job.error_message,
                )
                yield _sse_event(payload.model_dump(mode="json"))

            if job.status in TERMINAL_STATUSES:
                yield _sse_event({"done": True, "status": job.status})
                break

            await asyncio.sleep(SSE_POLL_INTERVAL)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering
        },
    )


def _sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"