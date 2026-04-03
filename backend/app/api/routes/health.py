from fastapi import APIRouter
from sqlalchemy import text

from backend.app.core.db import SessionLocal
from backend.app.core.metrics import metrics_response

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def readiness_check() -> dict[str, str]:
    session = SessionLocal()
    try:
        session.execute(text("SELECT 1"))
    finally:
        session.close()
    return {"status": "ready"}


@router.get("/metrics")
def metrics():
    return metrics_response()
