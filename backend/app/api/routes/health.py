from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import check_db_ready, get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "darukaa-ai-biodiversity-chatbot"}


@router.get("/health/ready")
def ready(db: Session = Depends(get_db)) -> dict:
    db_ok = False
    pgvector_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
        row = db.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        ).fetchone()
        pgvector_ok = row is not None
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "not_ready",
            "database": False,
            "pgvector": False,
            "error": str(exc),
        }
    status = "ready" if db_ok and pgvector_ok else "not_ready"
    return {
        "status": status,
        "database": db_ok,
        "pgvector": pgvector_ok,
        "check_db_ready": check_db_ready(),
    }
