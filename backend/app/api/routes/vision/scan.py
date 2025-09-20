from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from typing import Optional
import json, traceback

from app.core.config import VisionConfig
from app.services.vision.utils import decode_image
from app.services.vision.detector import detector
from app.services.vision.ocr import run_ocr
from app.services.vision.quality import calc_quality
from app.services.vision.matcher import get_match


router = APIRouter()


@router.post("/api/v1/vision/scan")
async def scan(
    image: UploadFile = File(...),
    guide_box: Optional[str] = Form(None),  # JSON 문자열 {"x":..,"y":..,"w":..,"h":..}
    user_query: Optional[str] = Form(None),
    request_id: Optional[str] = Form(None),
):
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_FILE_TYPE", "message": "Only JPEG/PNG"}},
        )

    content = await image.read()
    if len(content) > VisionConfig.MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "FILE_TOO_LARGE", "message": "Too large"}},
        )

    try:
        img, w, h = decode_image(content)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_FILE", "message": "Decode failed"}},
        )

    gb = None
    if guide_box:
        try:
            gb = json.loads(guide_box)
        except Exception:
            gb = None

    # --- 병 탐지 ---
    try:
        det = detector.detect(img, guide_box=gb)
    except Exception as e:
        print("detect error:", e)
        traceback.print_exc()
        det = {
            "present": False,
            "score": 0.0,
            "mask_polygon": None,
            "bbox": {"x": 0.0, "y": 0.0, "w": 0.0, "h": 0.0},
            "area_ratio": 0.0,
            "inside_ratio": 0.0,
        }

    # --- ROI: bbox 픽셀 좌표 계산 ---
    roi = None
    if det["bbox"]["w"] > 0 and det["bbox"]["h"] > 0:
        # bbox를 픽셀로 변환
        x = int(det["bbox"]["x"] * w)
        y = int(det["bbox"]["y"] * h)
        rw = int(det["bbox"]["w"] * w)
        rh = int(det["bbox"]["h"] * h)

        # bbox 세로 중앙 기준으로 라벨 높이 강제 확보(이미지의 50% 확보)
        cy = y + rh // 2
        target_h = max(int(0.5 * h), rh)  # 최소 50% 높이
        y = max(0, cy - target_h // 2)
        rh = min(h - y, target_h)

        # --- 패딩 적용 (더 넉넉하게) ---
        pad_x = max(20, int(0.15 * w))  # 가로 15% 여유
        pad_y = max(20, int(0.3 * h))  # 세로 30% 여유
        x = max(0, x - pad_x)
        y = max(0, y - pad_y)
        rw = min(w - x, rw + 2 * pad_x)
        rh = min(h - y, rh + 2 * pad_y)

        # --- ROI 최소 높이 보장 ---
        rh = max(rh, int(0.4 * h))

        roi = (x, y, rw, rh)

    print("ROI:", roi, "img shape:", img.shape)

    texts = run_ocr(img, roi=roi) if roi else []
    quality = calc_quality(img)
    match = get_match(texts, user_query or "")

    # ----- action 결정 로직 -----
    # 느슨한 자동이동 판정: "박스가 있고 + 점수/면적/품질이 최소 기준 통과 + 매칭됨"
    has_box = (det["bbox"]["w"] > 0) and (det["bbox"]["h"] > 0)

    # 점수는 보수적 임계의 절반 또는 0.10 중 높은 값으로 하한선을 둠
    min_score = max(0.10, getattr(VisionConfig, "THRESH_BOTTLE_SCORE", 0.2) * 0.5)
    good_score = det["score"] >= min_score

    # 너무 얇은 라인(오탐) 방지용 면적 하한만 둠 (상한은 굳이 두지 않음)
    good_area = det["area_ratio"] >= 0.02

    # 품질: 기존 기준 유지 + 눈뙤기(글레어) 상한이 있으면 반영
    max_glare = getattr(VisionConfig, "MAX_GLARE", 0.92)
    good_quality = (
        quality["blur"] >= VisionConfig.MIN_BLUR
        and quality["brightness"] >= VisionConfig.MIN_BRIGHTNESS
        and quality.get("glare_ratio", 0.0) <= max_glare
    )

    auto_ok = (
        has_box
        and good_score
        and good_area
        and (match["final"] is not None)
        and good_quality
    )

    action = "auto_advance" if auto_ok else "stay"

    resp = {
        "bottle": {
            "present": det["present"],
            "score": det["score"],
            "mask_polygon": det["mask_polygon"],
            "bbox": det["bbox"],
            "area_ratio": det["area_ratio"],
            "inside_ratio": det["inside_ratio"],
        },
        "texts": texts,
        "match": match,
        "quality": quality,
        "action": action,
        "timing": {"detect_ms": 0, "ocr_ms": 0, "match_ms": 0, "total_ms": 0},
        "request_id": request_id or "",
        "debug": None,
    }
    return resp
