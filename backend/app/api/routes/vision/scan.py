# backend/app/api/routes/vision/scan.py
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from typing import Optional
import json, traceback, time

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
    t0 = time.time()
    # ---------- 입력 검증 ----------
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

    # ---------- 디코드 ----------
    try:
        img, w, h = decode_image(content)
        print(f"[LOG][SCAN] image decoded: shape={img.shape}, w={w}, h={h}, request_id={request_id}")
    except Exception:
        print("[LOG][SCAN][ERROR] decode failed")
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_FILE", "message": "Decode failed"}},
        )

    # ---------- 가이드 박스 파싱 ----------
    gb = None
    if guide_box:
        try:
            gb = json.loads(guide_box)
            print(f"[LOG][SCAN] guide_box parsed: {gb}")
        except Exception:
            print(f"[LOG][SCAN][WARN] guide_box parse failed: {guide_box}")
            gb = None

    # ---------- 병 탐지 ----------
    t_det0 = time.time()
    try:
        det = detector.detect(img, guide_box=gb)
        print(f"[LOG][DETECT] result: present={det.get('present')}, score={det.get('score'):.3f}, "
              f"bbox={det.get('bbox')}, area_ratio={det.get('area_ratio'):.4f}, inside_ratio={det.get('inside_ratio')}")
    except Exception as e:
        print("[LOG][DETECT][ERROR] detect exception:", e)
        traceback.print_exc()
        det = {
            "present": False,
            "score": 0.0,
            "mask_polygon": None,
            "bbox": {"x": 0.0, "y": 0.0, "w": 0.0, "h": 0.0},
            "area_ratio": 0.0,
            "inside_ratio": 0.0,
        }
    t_det1 = time.time()

    # ---------- ROI 산출 (탐지 성공 시: bbox 기반, 실패 시: 백업 ROI) ----------
    roi = None
    if det["present"] and det["bbox"]["w"] > 0 and det["bbox"]["h"] > 0:
        # 1) 탐지 bbox → 픽셀
        x = int(det["bbox"]["x"] * w)
        y = int(det["bbox"]["y"] * h)
        rw = int(det["bbox"]["w"] * w)
        rh = int(det["bbox"]["h"] * h)

        # 2) 라벨 중앙 띠 확보(세로 최소 50% 확보)
        cy = y + rh // 2
        target_h = max(int(0.5 * h), rh)
        y = max(0, cy - target_h // 2)
        rh = min(h - y, target_h)

        # 3) 패딩 (UI/라벨 보정)
        pad_x = max(20, int(0.15 * w))
        pad_y = max(20, int(0.10 * h))
        x = max(0, x - pad_x)
        y = max(0, y - pad_y)
        rw = min(w - x, rw + 2 * pad_x)
        rh = min(h - y, rh + 2 * pad_y)

        roi = (x, y, rw, rh)
        print(f"[LOG][ROI] from detection bbox → roi={roi}")
    else:
        # 탐지 실패시 백업 ROI (중앙 60%x 높이는 60%, 상단 20% 오프셋)
        bw2 = int(w * 0.60)
        bh2 = int(h * 0.60)
        bx2 = (w - bw2) // 2
        by2 = int(h * 0.20)            # 위쪽 여백 조금 줌 (라벨 위치 고려)
        bh2 = min(h - by2, bh2)
        roi = (bx2, by2, bw2, bh2)
        print(f"[LOG][ROI] fallback roi used (no/weak detection): roi={roi}")

    # ---------- OCR ----------
    t_ocr0 = time.time()
    texts = []
    try:
        print(f"[LOG][OCR] start: roi={roi}, img_shape={img.shape}")
        texts = run_ocr(img, roi=roi)
        print(f"[LOG][OCR] done: {len(texts)} tokens → {texts}")
    except Exception as e:
        print("[LOG][OCR][ERROR] run_ocr exception:", e)
        traceback.print_exc()
        texts = []
    t_ocr1 = time.time()

    # ---------- 품질 ----------
    t_q0 = time.time()
    try:
        quality = calc_quality(img)
        print(f"[LOG][QUALITY] blur={quality.get('blur'):.2f}, "
              f"brightness={quality.get('brightness'):.3f}, "
              f"glare_ratio={quality.get('glare_ratio'):.3f}")
    except Exception as e:
        print("[LOG][QUALITY][ERROR] calc_quality exception:", e)
        traceback.print_exc()
        quality = {"blur": 0.0, "brightness": 0.0, "glare_ratio": 0.0}
    t_q1 = time.time()

    # ---------- 매칭 ----------
    t_m0 = time.time()
    try:
        match = get_match(texts, user_query or "")
        print(f"[LOG][MATCH] user_query={user_query} → final={match.get('final')}, "
              f"candidates={match.get('candidates')}")
    except Exception as e:
        print("[LOG][MATCH][ERROR] get_match exception:", e)
        traceback.print_exc()
        match = {"final": None, "candidates": []}
    t_m1 = time.time()

    # ---------- 자동 이동 판정(완화 기준) ----------
    has_box = (det["bbox"]["w"] > 0) and (det["bbox"]["h"] > 0)
    min_score = max(0.10, getattr(VisionConfig, "THRESH_BOTTLE_SCORE", 0.2) * 0.5)
    good_score = det["score"] >= min_score
    good_area  = det["area_ratio"] >= 0.02  # 너무 얇은 라인 방지
    max_glare  = getattr(VisionConfig, "MAX_GLARE", 0.92)
    good_quality = (
        quality["blur"] >= VisionConfig.MIN_BLUR and
        quality["brightness"] >= VisionConfig.MIN_BRIGHTNESS and
        quality.get("glare_ratio", 0.0) <= max_glare
    )
    auto_ok = has_box and good_score and good_area and (match["final"] is not None) and good_quality
    action = "auto_advance" if auto_ok else "stay"

    print(f"[LOG][ACTION] has_box={has_box}, score={det['score']:.3f} (min={min_score:.3f}), "
          f"area={det['area_ratio']:.3f}, quality_ok={good_quality}, "
          f"matched={match['final'] is not None} → action={action}")

    # ---------- 타이밍 ----------
    total_ms = int((time.time() - t0) * 1000)
    detect_ms = int((t_det1 - t_det0) * 1000)
    ocr_ms = int((t_ocr1 - t_ocr0) * 1000)
    match_ms = int((t_m1 - t_m0) * 1000)
    quality_ms = int((t_q1 - t_q0) * 1000)
    print(f"[LOG][TIME] total={total_ms}ms, detect={detect_ms}ms, ocr={ocr_ms}ms, "
          f"match={match_ms}ms, quality={quality_ms}ms")

    # ---------- 응답 ----------
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
        "timing": {
            "detect_ms": detect_ms,
            "ocr_ms": ocr_ms,
            "match_ms": match_ms,
            "quality_ms": quality_ms,
            "total_ms": total_ms
        },
        "request_id": request_id or "",
        "debug": None,
    }
    return resp
