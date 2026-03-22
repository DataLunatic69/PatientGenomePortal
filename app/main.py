import structlog
import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.config import settings
from app.api.routers import api_router
from app.database.session import init_db

logger = structlog.get_logger()


def create_app() -> FastAPI:
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[FastApiIntegration()],
        )

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.on_event("startup")
    async def on_startup() -> None:
        await init_db()
        logger.info("app.startup", version=settings.app_version)

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok", "version": settings.app_version}

    return app


app = create_app()