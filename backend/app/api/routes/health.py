from fastapi import APIRouter
from app.core.db import ping as db_ping
from app.services.vision.detector import get_detector
from app.core.config import settings

router = APIRouter(prefix="/api/v1", tags=["Health"])

@router.get("/health")
def health():
    db_ok = db_ping()
    detector = get_detector()
    vision_ready = detector.ready()
    return {
        "ok": bool(db_ok and vision_ready),
        "app": {"name": settings.APP_NAME, "env": settings.APP_ENV},
        "db": {"ok": db_ok},
        "vision": {"ready": vision_ready},
    }
