import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
import os
import uuid
from arq.connections import create_pool

from sqlmodel import select

from app.api.schemas import DnaFileRead, UploadResponse
from app.config import settings
from app.database.models.analysis_job import AnalysisJob, JobStatus
from app.database.models.dna_file import DnaFile, DnaFileSource
from app.database.models.user import User
from app.database.session import get_db
from app.graph.pipeline import run_analysis
from app.services.storage import upload_file, build_storage_path
from app.worker import REDIS_SETTINGS

logger = structlog.get_logger()

router = APIRouter()

ALLOWED_EXTENSIONS = {".txt", ".vcf", ".csv", ".gz"}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB


def _detect_source(filename: str, content_preview: str) -> DnaFileSource:
    """Detect DNA file format from filename and content."""
    name = filename.lower()
    if "ancestry" in name:
        return DnaFileSource.ANCESTRY
    if name.endswith(".vcf") or content_preview.startswith("##fileformat=VCF"):
        return DnaFileSource.VCF
    if "23andme" in name or "genome_" in name:
        return DnaFileSource.TWENTYTHREE_AND_ME
    return DnaFileSource.RAW


@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_dna_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: uuid.UUID = Form(...),
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    """
    Upload a DNA file (23andMe / VCF / Ancestry format).
    Stores the file in Supabase storage and triggers the analysis pipeline.
    Returns a job_id for polling status.
    """
    # Validate user exists
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate file extension
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension. Allowed extensions are: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 500MB)")

    content_preview = file_bytes[:200].decode("utf-8", errors="replace")
    source = _detect_source(filename, content_preview)

    # Use centralized upload logic to create collision-safe path
    tmp_job_id = str(uuid.uuid4())
    storage_path = build_storage_path(str(user_id), filename, tmp_job_id)

    try:
        await upload_file(file_bytes, storage_path, content_type="text/plain")
    except Exception as exc:
        logger.exception("upload.supabase_failed")
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {exc}")

    # Create DnaFile record
    dna_file = DnaFile(
        user_id=user_id,
        original_filename=file.filename or "unknown",
        source=source,
        storage_path=storage_path,
        file_size_bytes=len(file_bytes),
    )
    db.add(dna_file)
    await db.flush()  # get dna_file.id

    # Create AnalysisJob record
    job = AnalysisJob(dna_file_id=dna_file.id)
    db.add(job)
    await db.flush()

    await db.commit()

    # Kick off background analysis via ARQ Redis Worker
    redis = await create_pool(REDIS_SETTINGS)
    await redis.enqueue_job(
        "analysis_worker_task",
        str(job.id),
        str(dna_file.id),
        storage_path,
        source.value,
    )

    logger.info(
        "upload.complete",
        job_id=str(job.id),
        filename=file.filename,
        source=source,
    )

    return UploadResponse(
        dna_file_id=dna_file.id,
        job_id=job.id,
        message="File uploaded. Analysis started.",
    )