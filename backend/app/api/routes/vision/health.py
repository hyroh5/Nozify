from fastapi import APIRouter
from app.services.vision.detector import detector
from app.core.config import VisionConfig

router = APIRouter()

@router.get("/api/v1/vision/health")
def vision_health():
    return {
        "status": "ok" if detector.ready() else "warming_up",
        "device": VisionConfig.DEVICE,
        "model_loaded": detector.ready(),
        "ocr_ready": True  # 7단계에서 실제 OCR 준비 상태로 교체
    }
