import structlog
from supabase import create_client, Client

from app.config import settings

logger = structlog.get_logger()


def _client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_key)


async def upload_file(
    file_bytes: bytes,
    storage_path: str,
    content_type: str = "text/plain",
) -> str:
    """
    Upload a file to Supabase storage.
    Returns the storage path on success.
    """
    try:
        _client().storage.from_(settings.supabase_bucket_name).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type},
        )
        logger.info("storage.upload_ok", path=storage_path)
        return storage_path
    except Exception as exc:
        logger.exception("storage.upload_failed", path=storage_path)
        raise RuntimeError(f"Supabase upload failed: {exc}") from exc


async def download_file(storage_path: str) -> bytes:
    """
    Download a file from Supabase storage.
    Returns raw bytes.
    """
    try:
        data = _client().storage.from_(settings.supabase_bucket_name).download(
            storage_path
        )
        logger.info("storage.download_ok", path=storage_path)
        return data
    except Exception as exc:
        logger.exception("storage.download_failed", path=storage_path)
        raise RuntimeError(f"Supabase download failed: {exc}") from exc


async def delete_file(storage_path: str) -> None:
    """Delete a file from Supabase storage."""
    try:
        _client().storage.from_(settings.supabase_bucket_name).remove([storage_path])
        logger.info("storage.delete_ok", path=storage_path)
    except Exception as exc:
        logger.exception("storage.delete_failed", path=storage_path)
        raise RuntimeError(f"Supabase delete failed: {exc}") from exc


def build_storage_path(user_id: str, filename: str, job_id: str) -> str:
    """
    Construct a deterministic, collision-safe storage path.
    Format: {user_id}/{job_id}/{filename}
    """
    return f"{user_id}/{job_id}/{filename}"