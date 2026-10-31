from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, videos, analysis, yield_pred, reports

api_router = APIRouter()

api_router.include_router(health.router, prefix="", tags=["System"])
api_router.include_router(videos.router, prefix="/videos", tags=["Videos"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis & Findings"])
api_router.include_router(yield_pred.router, prefix="/yield", tags=["Yield Prediction"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
