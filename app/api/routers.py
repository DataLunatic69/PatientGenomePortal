from fastapi import APIRouter

from app.api.endpoints.v1 import upload, analysis, variants, auth

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"],
)
api_router.include_router(
    upload.router,
    prefix="/upload",
    tags=["upload"],
)
api_router.include_router(
    analysis.router,
    prefix="/jobs",
    tags=["analysis"],
)
api_router.include_router(
    variants.router,
    prefix="/variants",
    tags=["variants"],
)
