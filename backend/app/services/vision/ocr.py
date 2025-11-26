# backend/app/services/vision/ocr.py

from functools import lru_cache
from typing import List, Dict, Any, Optional
import numpy as np

from app.core.config import VisionConfig
from app.services.vision.utils import _load_cv2


_ocr_engine = None


def _get_ocr_engine():
    """
    PaddleOCR 엔진을 singleton 형태로 초기화해서 재사용.
    """
    global _ocr_engine
    if _ocr_engine is None:
        from paddleocr import PaddleOCR

        # VisionConfig.OCR_LANGS 에서 첫 번째 언어만 사용
        raw_lang = (VisionConfig.OCR_LANGS or "en").split(",")[0].strip().lower()
        # 환경에 eng라고 들어와도 PaddleOCR에서 인식하는 코드로 매핑
        if raw_lang == "eng":
            raw_lang = "en"
        if raw_lang == "kor":
            raw_lang = "korean"

        print(f"[OCR] init PaddleOCR lang={raw_lang}")

        # ⚠ 중요: use_gpu, show_log 같은 인자 절대 넣지 말 것
        _ocr_engine = PaddleOCR(
            lang=raw_lang
            # 필요하면 여기서만 천천히 옵션 늘리는 식으로
            # det=True, rec=True, use_angle_cls=True 등
        )

    return _ocr_engine



# ---------- 메인 OCR 함수 ----------

def run_ocr(img_bgr, roi=None) -> List[Dict[str, Any]]:
    cv2 = _load_cv2()
    h, w = img_bgr.shape[:2]
    print(f"[LOG][OCR] PaddleOCR 시작, ROI={roi if roi else '전체 이미지'}")

    # ROI 크롭
    if roi:
        x, y, rw, rh = roi
        crop = img_bgr[y:y+rh, x:x+rw]
    else:
        x, y, rw, rh = 0, 0, w, h
        crop = img_bgr

    # BGR -> RGB
    img_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)

    ocr = _get_ocr_engine()
    # 결과 형식: [ [ [box, (text, score)], ... ] ]
    result = ocr.ocr(img_rgb, cls=True)

    texts: List[Dict[str, Any]] = []

    if not result:
        print("[LOG][OCR] 결과 없음")
        return texts

    for line in result[0]:
        box, (txt, score) = line
        # box: 4점 좌표 [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        bx0, by0 = min(xs), min(ys)
        bx1, by1 = max(xs), max(ys)

        # ROI 좌표를 원본 좌표로 복원
        abs_x0 = bx0 + x
        abs_y0 = by0 + y
        abs_x1 = bx1 + x
        abs_y1 = by1 + y

        nx = clamp01(abs_x0 / w)
        ny = clamp01(abs_y0 / h)
        nw = clamp01((abs_x1 - abs_x0) / w)
        nh = clamp01((abs_y1 - abs_y0) / h)

        texts.append(
            {
                "text": str(txt).upper(),
                "confidence": float(score),
                "box": {"x": nx, "y": ny, "w": nw, "h": nh},
            }
        )

    # 간단 중복 제거
    dedup = {}
    for r in texts:
        key = (r["text"], round(r["box"]["x"], 3), round(r["box"]["y"], 3))
        if key not in dedup or r["confidence"] > dedup[key]["confidence"]:
            dedup[key] = r

    texts = list(dedup.values())
    print(f"[LOG][OCR] PaddleOCR 결과 토큰 수={len(texts)}, texts={texts}")
    return texts

# ---------- 회전 OCR: Paddle 버전에서는 그냥 run_ocr 재사용 ----------

def run_ocr_rotated(img_bgr, roi=None, angles=None):
    # PaddleOCR 자체가 어느 정도 기울기 보정 / 각도 분류를 해주므로
    # 별도로 회전 스캔하지 않고 동일 함수 재사용
    return run_ocr(img_bgr, roi=roi)
