from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ───────────────────────────────────────────────────────────────────
    app_name: str = "Patient Genome Portal"
    app_version: str = "0.1.0"
    debug: bool = False
    allowed_origins: list[str] = ["http://localhost:3000"]


    # ── JWT Authentication ────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "super_secret_key_12345_change_in_production"
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