# backend/app/api/routes/vision/scan.py
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from typing import Optional
import json, traceback, time

import numpy as np

from app.core.config import VisionConfig
from app.services.vision.utils import decode_image, clamp01
from app.services.vision.detector import get_detector
from app.services.vision.ocr import run_ocr, run_ocr_rotated
from app.services.vision.quality import calc_quality
from app.services.vision.matcher import get_match

router = APIRouter(tags=["vision"])



def _roi_from_bbox(bbox, w, h):
    """
    탐지 bbox → OCR용 ROI 확보 + 패딩
    [수정]: 탐지 실패 (무효한 bbox) 시 ROI를 이미지 중앙 전체(90%)로 확장
    """
    
    # 1. 탐지 실패 여부 확인 (w나 h가 0인 경우)
    if bbox["w"] <= 0.0 or bbox["h"] <= 0.0:
        # [Fallback 로직 확장] 이미지 중앙 90% 영역을 ROI로 사용 (Full Scan에 가까움)
        x = int(w * 0.05)
        y = int(h * 0.05)
        rw = int(w * 0.9)
        rh = int(h * 0.9)
        
        rw = max(1, rw)
        rh = max(1, rh)
        
        return (x, y, rw, rh)
        
    # 2. 탐지 성공 시 기존 로직 실행 (로직 동일)
    
    x = int(bbox["x"] * w)
    y = int(bbox["y"] * h)
    rw = int(bbox["w"] * w)
    rh = int(bbox["h"] * h)

    target_h = max(int(0.7 * rh), 100) 
    y_start = int(y + 0.1 * rh)
    
    y = max(0, y_start)
    rh = min(h - y, target_h)
    
    pad_x = max(20, int(0.15 * rw))
    pad_y = max(10, int(0.15 * rh)) 
    
    x = max(0, x - pad_x)
    y = max(0, y - pad_y)
    rw = min(w - x, rw + 2 * pad_x)
    rh = min(h - y, rh + 2 * pad_y)

    rw = max(1, rw)
    rh = max(1, rh)

    return (x, y, rw, rh)

def _fallback_roi(w, h):
    """
    [수정] _roi_from_bbox 함수의 Fallback 로직이 이 함수를 대체하도록 했습니다. 
    이 함수는 이제 사용되지 않거나, 내부적으로 _roi_from_bbox에 통합된 로직을 그대로 반환합니다.
    """
    # 원본 _fallback_roi를 유지하되, _roi_from_bbox의 Fallback 로직이 더 넓어 사용하지 않습니다.
    bw2 = int(w * 0.60)
    bh2 = int(h * 0.60)
    bx2 = (w - bw2) // 2
    by2 = int(h * 0.20)
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
        alnum_like = sum(ch.isalnum() or ch in "°" for ch in txt)
        if alnum_like < 2:
            continue
        b = t.get("box") or {}
        if b.get("w", 0) <= 0.02 or b.get("h", 0) <= 0.01:
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

    # 패딩 라벨 주변 넉넉히
    pad_x = int(0.25 * (x1 - x0))
    pad_y = int(0.20 * (y1 - y0))
    x0 = max(0, x0 - pad_x)
    y0 = max(0, y0 - pad_y)
    x1 = min(w, x1 + pad_x)
    y1 = min(h, y1 + pad_y)
    return (x0, y0, x1 - x0, y1 - y0)


def dedup_merge(list1, list2):
    """같은 텍스트 근처 위치는 높은 confidence로 병합"""
    out = {}
    for r in list1 + list2:
        key = (r["text"], round(r["box"]["x"], 3), round(r["box"]["y"], 3))
        if key not in out or r["confidence"] > out[key]["confidence"]:
            out[key] = r
    return list(out.values())


def merge_texts_by_line(texts, y_tol: float = 0.02):
    """
    y 중심이 비슷한 텍스트들을 한 줄로 묶어서 반환.
    matcher에는 이 병합 결과를 넘기고,
    원본 texts는 그대로 응답에 포함시킨다.
    """
    if not texts:
        return []

    lines = {}
    for t in texts:
        b = t.get("box", {})
        cy = b.get("y", 0.0) + b.get("h", 0.0) / 2.0
        key = round(cy / y_tol) * y_tol
        lines.setdefault(key, []).append(t)

    merged = []
    for _, items in lines.items():
        items = sorted(items, key=lambda r: r["box"]["x"])

        line_text = " ".join(r["text"] for r in items)

        xs = [r["box"]["x"] for r in items]
        ys = [r["box"]["y"] for r in items]
        ws = [r["box"]["w"] for r in items]
        hs = [r["box"]["h"] for r in items]

        x0 = min(xs)
        y0 = min(ys)
        x1 = max(x + w for x, w in zip(xs, ws))
        y1 = max(y + h for y, h in zip(ys, hs))

        merged.append(
            {
                "text": line_text,
                "confidence": max(r["confidence"] for r in items),
                "box": {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0},
            }
        )

    print(f"[LOG][OCR] merged lines: {merged}")
    return merged


@router.post("/scan")
async def scan(
    image: UploadFile = File(...),
    guide_box: Optional[str] = Form(None),
    user_query: Optional[str] = Form(None),
    request_id: Optional[str] = Form(None),
):
    t0 = time.time()

    # 여기서만 cv2 로드 서버 부팅에서는 절대 로드하지 않음
    try:
        import cv2
    except Exception as e:
        print("[LOG][SCAN][ERROR] OpenCV import failed:", e)
        raise HTTPException(
            status_code=503,
            detail={"error": {"code": "OPENCV_LOAD_FAIL", "message": str(e)}},
        )

    print("[SCAN] Received image:", image.filename, image.content_type)

    content_preview = await image.read()
    print("[SCAN] Image length (bytes):", len(content_preview))

    image.file.seek(0)

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
        detector = get_detector()
        if not detector.ready():
            raise HTTPException(status_code=503, detail="Vision model not ready")

        det = detector.detect(img, guide_box=gb)
        print(
            f"[LOG][DETECT] result: present={det.get('present')}, "
            f"score={det.get('score'):.3f}, bbox={det.get('bbox')}, "
            f"area_ratio={det.get('area_ratio'):.4f}"
        )
    except HTTPException:
        raise
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
    area_ratio = det.get("area_ratio", 0.0)
    # [수정] area_ratio 임계값을 0.02에서 0.005로 낮춰 저해상도 이미지의 작은 탐지 결과도 허용
    if det["bbox"]["w"] > 0 and det["bbox"]["h"] > 0 and area_ratio >= 0.005: 
        roi = _roi_from_bbox(det["bbox"], w, h)
        print(f"[LOG][ROI] from detection bbox → roi={roi}, area_ratio={area_ratio:.4f}")
    else:
        # _roi_from_bbox의 Fallback 로직(_bbox["w"] <= 0.0)이 이미 넓은 영역을 반환하도록 수정되었으므로,
        # 탐지 실패 시 여기서도 해당 로직을 실행. _fallback_roi는 사용하지 않음.
        roi_bbox_dummy = {"x": 0.0, "y": 0.0, "w": 0.0, "h": 0.0}
        roi = _roi_from_bbox(roi_bbox_dummy, w, h)
        print(f"[LOG][ROI] fallback roi → roi={roi}, area_ratio={area_ratio:.4f}")


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
    
    # ---------- 회전 OCR 보강 ----------
    # [수정] run_ocr이 텍스트를 인식하지 못했거나(len(texts) == 0), 신뢰도 높은 텍스트가 부족하면 run_ocr_rotated 실행
    if len(texts) == 0 or len([t for t in texts if t.get("confidence", 0) >= 0.80]) < 3:
        rot_texts = run_ocr_rotated(img, roi=roi)
        if rot_texts:
            texts = dedup_merge(texts, rot_texts)
            print(f"[LOG][OCR] rotated merge → {len(texts)} tokens")

    t_ocr1 = time.time()


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
                            # [수정] 재탐지 후 OCR 재실행 시에도 회전 OCR을 포함시켜 완전한 재시도를 유도
                            texts = run_ocr(img, roi=roi)
                            if len(texts) == 0 or len([t for t in texts if t.get("confidence", 0) >= 0.80]) < 3:
                                rot_texts = run_ocr_rotated(img, roi=roi)
                                if rot_texts:
                                    texts = dedup_merge(texts, rot_texts)
                            print(f"[LOG][OCR] re-run after redetect: {len(texts)} tokens")
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
        merged_texts = merge_texts_by_line(texts)
        match = get_match(merged_texts, user_query or "")
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
    # [수정] good_area 임계값을 0.02에서 0.005로 낮춰 탐지 실패 조건 완화
    good_area = det["area_ratio"] >= 0.005 
    max_glare = getattr(VisionConfig, "MAX_GLARE", 0.92)
    good_quality = (
        quality["blur"] >= VisionConfig.MIN_BLUR
        and quality["brightness"] >= VisionConfig.MIN_BRIGHTNESS
        and quality.get("glare_ratio", 0.0) <= max_glare
    )
    auto_ok = has_box and good_score and good_area and (match["final"] is not None) and good_quality
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

