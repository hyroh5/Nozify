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
from app.services.vision.utils import clamp01  # 좌표 보정용

router = APIRouter()


def _roi_from_bbox(bbox, w, h):
    """탐지 bbox → OCR용 ROI(라벨 중앙 띠 확보 + 패딩)"""
    x = int(bbox["x"] * w)
    y = int(bbox["y"] * h)
    rw = int(bbox["w"] * w)
    rh = int(bbox["h"] * h)

    # 라벨 중앙 띠 확보(세로 최소 50% 확보)
    cy = y + rh // 2
    target_h = max(int(0.5 * h), rh)
    y = max(0, cy - target_h // 2)
    rh = min(h - y, target_h)

    # 패딩
    pad_x = max(20, int(0.15 * w))
    pad_y = max(20, int(0.10 * h))
    x = max(0, x - pad_x)
    y = max(0, y - pad_y)
    rw = min(w - x, rw + 2 * pad_x)
    rh = min(h - y, rh + 2 * pad_y)
    return (x, y, rw, rh)


def _fallback_roi(w, h):
    """탐지 실패 시 중앙부 백업 ROI"""
    bw2 = int(w * 0.60)
    bh2 = int(h * 0.60)
    bx2 = (w - bw2) // 2
    by2 = int(h * 0.20)  # 라벨 고려하여 위 여백
    bh2 = min(h - by2, bh2)
    return (bx2, by2, bw2, bh2)


def _text_guided_roi(texts, w, h):
    """신뢰 높은 텍스트들을 묶어 재탐지용 ROI 생성"""
    good = []
    for t in texts:
        txt = (t.get("text") or "").upper()
        conf = float(t.get("confidence", 0))
        if conf < 0.80:
            continue
        # 영/숫/° 위주이며 최소 2자
        alnum_like = sum(ch.isalnum() or ch in "°" for ch in txt)
        if alnum_like < 2:
            continue
        b = t.get("box") or {}
        # 너무 작은 기호/노이즈 컷
        if b.get("w", 0) <= 0.02 or b.get("h", 0) <= 0.01:
            continue
        good.append(b)

    if not good:
        return None

    xs = [int(b["x"] * w) for b in good]
    ys = [int(b["y"] * h) for b in good]
    x2s = [int((b["x"] + b["w"]) * w) for b in good]
    y2s = [int((b["y"] + b["h"]) * h) for b in good]
    x0, y0 = max(0, min(xs)), max(0, min(ys))
    x1, y1 = min(w - 1, max(x2s)), min(h - 1, max(y2s))
    rw, rh = x1 - x0, y1 - y0
    if rw <= 0 or rh <= 0:
        return None

    # 텍스트 주변 넉넉히 패딩
    pad_x = max(int(0.15 * w), 20)
    pad_y = max(int(0.20 * h), 20)
    x = max(0, x0 - pad_x)
    y = max(0, y0 - pad_y)
    rw = min(w - x, rw + 2 * pad_x)
    rh = min(h - y, rh + 2 * pad_y)
    return (x, y, rw, rh)


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
        print(
            f"[LOG][DETECT] result: present={det.get('present')}, score={det.get('score'):.3f}, "
            f"bbox={det.get('bbox')}, area_ratio={det.get('area_ratio'):.4f}, inside_ratio={det.get('inside_ratio')}"
        )
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
    if det["bbox"]["w"] > 0 and det["bbox"]["h"] > 0:
        roi = _roi_from_bbox(det["bbox"], w, h)
        print(f"[LOG][ROI] from detection bbox → roi={roi}")
    else:
        roi = _fallback_roi(w, h)
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

    # ---------- 텍스트-가이드 재탐지(초기 탐지 약할 때만) ----------
    redetected = False
    if (not det.get("present", False) or det.get("score", 0.0) < 0.15) and len(texts) >= 2 and getattr(detector, "yolo", None) is not None:
        tg_roi = _text_guided_roi(texts, w, h)
        if tg_roi is not None:
            tx, ty, tw, th = tg_roi
            crop = img[ty:ty+th, tx:tx+tw]
            try:
                res2 = detector.yolo.predict(
                    crop[:, :, ::-1],
                    imgsz=1280,
                    conf=0.03,
                    iou=0.45,
                    classes=None,
                    agnostic_nms=True,
                    verbose=False,
                )[0]
                if res2.boxes is not None and len(res2.boxes) > 0:
                    import numpy as np
                    confs = res2.boxes.conf.cpu().numpy()
                    xywhn = res2.boxes.xywhn.cpu().numpy()
                    best = int(np.argmax(confs))
                    top_conf = float(confs[best])
                    cx, cy, bw, bh = map(float, xywhn[best])

                    # 크롭 → 원본 좌표 복원
                    bx = clamp01((tx + (cx - bw/2) * tw) / w)
                    by = clamp01((ty + (cy - bh/2) * th) / h)
                    bw = clamp01(bw * (tw / w))
                    bh = clamp01(bh * (th / h))

                    new_det = {
                        "present": top_conf >= detector.score_th,
                        "score": top_conf,
                        "mask_polygon": None,
                        "bbox": {"x": bx, "y": by, "w": bw, "h": bh},
                        "area_ratio": bw * bh,
                        "inside_ratio": 1.0,
                    }

                    # 기존보다 명확하면 교체
                    if top_conf > det.get("score", 0.0):
                        print(f"[LOG][REDETECT] text-guided applied: conf {det['score']:.3f} → {top_conf:.3f}, bbox={new_det['bbox']}")
                        det = new_det
                        redetected = True

                        # 새 bbox로 ROI/ OCR 재수행(1회)
                        roi = _roi_from_bbox(det["bbox"], w, h)
                        print(f"[LOG][ROI] re-ocr with new bbox → roi={roi}")
                        try:
                            t_ocr0b = time.time()
                            texts = run_ocr(img, roi=roi)
                            t_ocr1b = time.time()
                            print(f"[LOG][OCR] re-run done: {len(texts)} tokens (Δ={int((t_ocr1b-t_ocr0b)*1000)}ms)")
                            # OCR 시간 합산
                            t_ocr1 = t_ocr1b
                        except Exception as e:
                            print("[LOG][OCR][ERROR] re-run after redetect:", e)
            except Exception as e:
                print("[LOG][REDETECT][ERROR]:", e)

    # ---------- 품질 ----------
    t_q0 = time.time()
    try:
        quality = calc_quality(img)
        print(
            f"[LOG][QUALITY] blur={quality.get('blur'):.2f}, "
            f"brightness={quality.get('brightness'):.3f}, "
            f"glare_ratio={quality.get('glare_ratio'):.3f}"
        )
    except Exception as e:
        print("[LOG][QUALITY][ERROR] calc_quality exception:", e)
        traceback.print_exc()
        quality = {"blur": 0.0, "brightness": 0.0, "glare_ratio": 0.0}
    t_q1 = time.time()

    # ---------- 매칭 ----------
    t_m0 = time.time()
    try:
        match = get_match(texts, user_query or "")
        print(
            f"[LOG][MATCH] user_query={user_query} → final={match.get('final')}, "
            f"candidates={match.get('candidates')}"
        )
    except Exception as e:
        print("[LOG][MATCH][ERROR] get_match exception:", e)
        traceback.print_exc()
        match = {"final": None, "candidates": []}
    t_m1 = time.time()

    # ---------- 자동 이동 판정(완화 기준) ----------
    has_box = (det["bbox"]["w"] > 0) and (det["bbox"]["h"] > 0)
    min_score = max(0.10, getattr(VisionConfig, "THRESH_BOTTLE_SCORE", 0.2) * 0.5)
    good_score = det["score"] >= min_score
    good_area = det["area_ratio"] >= 0.02  # 너무 얇은 라인 방지
    max_glare = getattr(VisionConfig, "MAX_GLARE", 0.92)
    good_quality = (
        quality["blur"] >= VisionConfig.MIN_BLUR
        and quality["brightness"] >= VisionConfig.MIN_BRIGHTNESS
        and quality.get("glare_ratio", 0.0) <= max_glare
    )
    auto_ok = has_box and good_score and good_area and (match["final"] is not None) and good_quality
    action = "auto_advance" if auto_ok else "stay"

    print(
        f"[LOG][ACTION] has_box={has_box}, score={det['score']:.3f} (min={min_score:.3f}), "
        f"area={det['area_ratio']:.3f}, quality_ok={good_quality}, "
        f"matched={match['final'] is not None} → action={action}"
    )

    # ---------- 타이밍 ----------
    total_ms = int((time.time() - t0) * 1000)
    detect_ms = int((t_det1 - t_det0) * 1000)
    ocr_ms = int((t_ocr1 - t_ocr0) * 1000)
    match_ms = int((t_m1 - t_m0) * 1000)
    quality_ms = int((t_q1 - t_q0) * 1000)
    print(
        f"[LOG][TIME] total={total_ms}ms, detect={detect_ms}ms, ocr={ocr_ms}ms, "
        f"match={match_ms}ms, quality={quality_ms}ms, redetect={redetected}"
    )

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
            "total_ms": total_ms,
        },
        "request_id": request_id or "",
        "debug": {"redetect": redetected},
    }
    return resp
