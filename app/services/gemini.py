"""
Shared Gemini helper — handles retries with exponential backoff and
falls back to a lighter model when the primary (gemini-2.5-pro) is
unavailable due to 503 / 429 quota errors.
"""
import logging
import time

from google import genai

logger = logging.getLogger(__name__)

_PRIMARY_MODEL = "gemini-2.5-pro"
_FALLBACK_MODEL = "gemini-2.0-flash"


def generate_with_retry(
    client: genai.Client,
    prompt: str,
    max_retries: int = 3,
) -> str:
    """
    Generate content with exponential backoff retries.
    Tries _PRIMARY_MODEL first; if all retries fail on transient errors,
    tries _FALLBACK_MODEL.  Raises the last exception if everything fails.
    """
    last_exc: Exception | None = None

    for model in (_PRIMARY_MODEL, _FALLBACK_MODEL):
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                return (response.text or "").strip()
            except Exception as exc:
                last_exc = exc
                err_str = str(exc)
                is_transient = any(
                    kw in err_str
                    for kw in ("503", "429", "UNAVAILABLE", "quota", "Resource has been exhausted")
                )
                if is_transient:
                    wait = 2 ** attempt  # 1 s, 2 s, 4 s
                    logger.warning(
                        "gemini.retry",
                        extra={
                            "model": model,
                            "attempt": attempt + 1,
                            "wait_seconds": wait,
                            "error": err_str[:200],
                        },
                    )
                    time.sleep(wait)
                else:
                    logger.warning(
                        "gemini.non_retryable",
                        extra={"model": model, "error": err_str[:200]},
                    )
                    break  # skip remaining retries for this model

        logger.warning("gemini.model_exhausted", extra={"model": model})

    raise last_exc or RuntimeError("Gemini generation failed after all retries")
