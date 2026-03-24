import json

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_cors_origins(raw: str) -> list[str]:
    """
    Accept plain env strings from platforms like Render:
    - *  (allow all)
    - https://a.com,https://b.com
    - ["https://a.com","https://b.com"]
    """
    value = (raw or "").strip()
    # Mis-pasted env line used as the value (e.g. ALLOWED_ORIGINS=ALLOWED_ORIGINS = [...])
    if "ALLOWED_ORIGINS" in value:
        return ["*"]
    if not value:
        return ["*"]
    if value == "*":
        return ["*"]
    if value.startswith("["):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                out = [str(x).strip() for x in parsed if str(x).strip()]
                return out if out else ["*"]
        except json.JSONDecodeError:
            pass
    parts = [p.strip() for p in value.split(",") if p.strip()]
    return parts if parts else ["*"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Empty ALLOWED_ORIGINS on Render must not be JSON-decoded as a list
        env_ignore_empty=True,
    )

    # ── App ───────────────────────────────────────────────────────────────────
    app_name: str = "Patient Genome Portal"
    app_version: str = "0.1.0"
    debug: bool = False
    # Plain str + alias: pydantic-settings must not treat this as JSON (list/dict).
    # Do not use @computed_field for cors_origins — list[str] is loaded via json.loads from env.
    allowed_origins_raw: str = Field(
        default="*",
        validation_alias="ALLOWED_ORIGINS",
    )

    @property
    def cors_origins(self) -> list[str]:
        return _parse_cors_origins(self.allowed_origins_raw)


    # ── JWT Authentication ────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "33565a08a5a7310a84e0c5b43fec2e756f37332047f78dc577e54ef7a74180294449f7f1c548664313c206bdda8369aea26d2ec18a2e524278575fc04587f042"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── API Keys ──────────────────────────────────────────────────────────────
    alphagenome_api_key: str
    gemini_api_key: str

    # ── Database (Supabase Postgres) ──────────────────────────────────────────
    database_url: PostgresDsn

    # ── Redis (ARQ Worker) ────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Supabase Storage ──────────────────────────────────────────────────────
    supabase_url: str
    supabase_service_key: str        # service role key — backend only
    supabase_bucket_name: str = "dna-files"

    # ── AlphaGenome ───────────────────────────────────────────────────────────
    sequence_length: str = "1MB"
    max_variants_to_score: int = 500
    max_variants_to_visualize: int = 10

    # ── Sentry ────────────────────────────────────────────────────────────────
    sentry_dsn: str = ""


settings = Settings()  # type: ignore[call-arg]