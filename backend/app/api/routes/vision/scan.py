# backend/app/api/routes/vision/scan.py
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from typing import Optional
import json, traceback, time

import numpy as np
import cv2

from app.core.config import VisionConfig
from app.services.vision.utils import decode_image, clamp01  # 좌표 보정용
from app.services.vision.detector import detector
from app.services.vision.ocr import run_ocr, run_ocr_rotated
from app.services.vision.quality import calc_quality
from app.services.vision.matcher import get_match

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
        if conf < 0.80:  # 3-2: 올림
            continue
        alnum_like = sum(ch.isalnum() or ch in "°" for ch in txt)
        if alnum_like < 2:
            continue
        b = t.get("box") or {}
        if b.get("w", 0) <= 0.02 or b.get("h", 0) <= 0.01:  # 작은 노이즈 컷
            continue
        good.append(b)

    if not good:
        return None

    xs = [int(b["x"] * w) for b in good]
    ys = [int(b["y"] * h) for b in good]
    x2 = [int((b["x"] + b["w"]) * w) for b in good]
    y2 = [int((b["y"] + b["h"]) * h) for b in good]
    x0, y0 = max(0, min(xs)), max(0, min(ys))
    x1, y1 = min(w, max(x2)), min(h, max(y2))

    # 패딩(라벨 주변 넉넉히)
    pad_x = int(0.25 * (x1 - x0))
    pad_y = int(0.20 * (y1 - y0))
    x0 = max(0, x0 - pad_x)
    y0 = max(0, y0 - pad_y)
    x1 = min(w, x1 + pad_x)
    y1 = min(h, y1 + pad_y)
    return (x0, y0, x1 - x0, y1 - y0)


def dedup_merge(list1, list2):
    """같은 텍스트/근처 위치는 높은 confidence로 병합"""
    out = {}
    for r in list1 + list2:
        key = (r["text"], round(r["box"]["x"], 3), round(r["box"]["y"], 3))
        if key not in out or r["confidence"] > out[key]["confidence"]:
            out[key] = r
    return list(out.values())


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
        print(
            f"[LOG][SCAN] image decoded: shape={img.shape}, w={w}, h={h}, request_id={request_id}"
        )
    except Exception:
        print("[LOG][SCAN][ERROR] decode failed")
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_FILE", "message": "Decode failed"}},
        )

    # ---------- 가이드 박스 ----------
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
            f"[LOG][DETECT] result: present={det.get('present')}, "
            f"score={det.get('score'):.3f}, bbox={det.get('bbox')}, "
            f"area_ratio={det.get('area_ratio'):.4f}"
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

    # ---------- ROI ----------
    if det["bbox"]["w"] > 0 and det["bbox"]["h"] > 0:
        roi = _roi_from_bbox(det["bbox"], w, h)
        print(f"[LOG][ROI] from detection bbox → roi={roi}")
    else:
        roi = _fallback_roi(w, h)
        print(f"[LOG][ROI] fallback roi → roi={roi}")

    # ---------- OCR ----------
    t_ocr0 = time.time()
    texts = []
    try:
        print(f"[LOG][OCR] start: roi={roi}, img_shape={img.shape}")
        texts = run_ocr(img, roi=roi)
        print(f"[LOG][OCR] done: {len(texts)} tokens")
    except Exception as e:
        print("[LOG][OCR][ERROR]", e)
        traceback.print_exc()
        texts = []
    t_ocr1 = time.time()

    # ---------- 회전 OCR 보강 ----------
    if len([t for t in texts if t.get("confidence", 0) >= 0.80]) < 3:
        rot_texts = run_ocr_rotated(img, roi=roi)
        if rot_texts:
            texts = dedup_merge(texts, rot_texts)
            print(f"[LOG][OCR] rotated merge → {len(texts)} tokens")

    # ---------- 텍스트 기반 재탐지 ----------
    redetected = False
    if (
        (not det.get("present", False) or det.get("score", 0.0) < 0.15)
        and len(texts) >= 2
        and getattr(detector, "yolo", None)
    ):
        tg_roi = _text_guided_roi(texts, w, h)
        if tg_roi is not None:
            tx, ty, tw, th = tg_roi
            crop = img[ty : ty + th, tx : tx + tw]
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
                    confs = res2.boxes.conf.cpu().numpy()
                    xywhn = res2.boxes.xywhn.cpu().numpy()
                    best = int(np.argmax(confs))
                    top_conf = float(confs[best])
                    cx, cy, bw, bh = map(float, xywhn[best])

                    # 크롭 → 원본 좌표 복원
                    bx = clamp01((tx + (cx - bw / 2) * tw) / w)
                    by = clamp01((ty + (cy - bh / 2) * th) / h)
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
                    if top_conf > det.get("score", 0.0):
                        print(
                            f"[LOG][REDETECT] applied: {det['score']:.3f} → {top_conf:.3f}, bbox={new_det['bbox']}"
                        )
                        det = new_det
                        redetected = True
                        roi = _roi_from_bbox(det["bbox"], w, h)
                        try:
                            texts = run_ocr(img, roi=roi)
                            print(
                                f"[LOG][OCR] re-run after redetect: {len(texts)} tokens"
                            )
                        except Exception as e:
                            print("[LOG][OCR][ERROR] re-run:", e)
            except Exception as e:
                print("[LOG][REDETECT][ERROR]:", e)

    # ---------- 품질 ----------
    t_q0 = time.time()
    try:
        quality = calc_quality(img)
        print(
            f"[LOG][QUALITY] blur={quality.get('blur'):.2f}, "
            f"bright={quality.get('brightness'):.3f}, glare={quality.get('glare_ratio'):.3f}"
        )
    except Exception as e:
        print("[LOG][QUALITY][ERROR]", e)
        traceback.print_exc()
        quality = {"blur": 0.0, "brightness": 0.0, "glare_ratio": 0.0}
    t_q1 = time.time()

    # ---------- 매칭 ----------
    t_m0 = time.time()
    try:
        match = get_match(texts, user_query or "")
        print(
            f"[LOG][MATCH] → final={match.get('final')}, candidates={match.get('candidates')}"
        )
    except Exception as e:
        print("[LOG][MATCH][ERROR]", e)
        traceback.print_exc()
        match = {"final": None, "candidates": []}
    t_m1 = time.time()

    # ---------- 액션 ----------
    has_box = (det["bbox"]["w"] > 0) and (det["bbox"]["h"] > 0)
    min_score = max(0.10, getattr(VisionConfig, "THRESH_BOTTLE_SCORE", 0.2) * 0.5)
    good_score = det["score"] >= min_score
    good_area = det["area_ratio"] >= 0.02
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
    print(
        f"[LOG][ACTION] has_box={has_box}, score={det['score']:.3f}, area={det['area_ratio']:.3f}, "
        f"quality_ok={good_quality}, matched={match['final'] is not None} → {action}"
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
    return {
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
