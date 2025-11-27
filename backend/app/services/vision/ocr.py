# backend/app/services/vision/ocr.py
from typing import List, Dict, Any, Optional, Union
import numpy as np

from paddleocr import PaddleOCR

from .utils import _load_cv2
from app.core.config import VisionConfig

_ocr_engine: Optional[PaddleOCR] = None


def _get_ocr_engine() -> PaddleOCR:
    """
    PaddleOCR 엔진을 lazy-init 로드
    """
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = PaddleOCR(
            use_angle_cls=True,
            lang="en",
            use_gpu=False,
        )
    return _ocr_engine


def _parse_roi(
    roi: Union[Dict[str, float], List[float], tuple],
    w: int,
    h: int,
) -> Optional[Dict[str, int]]:
    """
    roi 를 dict(x,y,w,h) 또는 (x, y, w, h) 튜플/리스트 둘 다 지원해서
    실제 픽셀 좌표로 변환
    """
    if roi is None:
        return None

    # dict 형태
    if isinstance(roi, dict):
        x_norm = float(roi.get("x", 0.0))
        y_norm = float(roi.get("y", 0.0))
        w_norm = float(roi.get("w", 1.0))
        h_norm = float(roi.get("h", 1.0))

    # tuple/list 형태
    elif isinstance(roi, (list, tuple)) and len(roi) == 4:
        x_norm = float(roi[0])
        y_norm = float(roi[1])
        w_norm = float(roi[2])
        h_norm = float(roi[3])
    else:
        # 이상한 형식이면 전체 이미지 사용
        return None

    x = int(x_norm * w)
    y = int(y_norm * h)
    rw = int(w_norm * w)
    rh = int(h_norm * h)

    x = max(0, min(x, w - 1))
    y = max(0, min(y, h - 1))
    rw = max(1, min(rw, w - x))
    rh = max(1, min(rh, h - y))

    return {"x": x, "y": y, "w": rw, "h": rh}


def run_ocr(
    img_bgr,
    roi: Optional[Union[Dict[str, float], List[float], tuple]] = None,
) -> List[Dict[str, Any]]:
    """
    img_bgr: BGR numpy array (H, W, 3)
    roi: 정규화 좌표
         - dict: {"x":0~1,"y":0~1,"w":0~1,"h":0~1}
         - tuple/list: (x, y, w, h) in 0~1
    """
    cv2 = _load_cv2()
    h, w = img_bgr.shape[:2]

    roi_px = _parse_roi(roi, w, h) if roi is not None else None
    if roi_px is not None:
        x = roi_px["x"]
        y = roi_px["y"]
        rw = roi_px["w"]
        rh = roi_px["h"]
        crop = img_bgr[y:y + rh, x:x + rw]
    else:
        x, y = 0, 0
        crop = img_bgr

    ocr = _get_ocr_engine()

    # PaddleOCR 결과: 보통 [ [ [box, (text, score)], ... ] ] 형태
    result = ocr.ocr(crop, cls=True)

    texts: List[Dict[str, Any]] = []

    # None 이거나 비어있으면 바로 반환
    if not result:
        return texts

    # result 가 리스트가 아닌 형태로 올 가능성까지 방어
    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
        lines = result[0]
    else:
        # 구조가 예상과 다르면 전체를 lines 로 취급
        lines = result

    for line in lines:
        try:
            box, (txt, score) = line  # box: 4x2, txt: str, score: float
        except Exception:
            # 구조가 다르면 스킵
            continue

        box = np.array(box, dtype=np.float32)

        # crop 기준 → 원본 기준, 정규화
        xs = (box[:, 0] + x) / w
        ys = (box[:, 1] + y) / h

        bx = float(xs.min())
        by = float(ys.min())
        bw = float(xs.max() - xs.min())
        bh = float(ys.max() - ys.min())

        texts.append(
            {
                "text": txt,
                "confidence": float(score),
                "box": {"x": bx, "y": by, "w": bw, "h": bh},
            }
        )

    return texts


def run_ocr_rotated(
    img_bgr,
    roi: Optional[Union[Dict[str, float], List[float], tuple]] = None,
) -> List[Dict[str, Any]]:
    """
    현재는 단순히 run_ocr 래핑.
    나중에 회전까지 돌리고 싶으면 여기서 추가 구현.
    """
    return run_ocr(img_bgr, roi=roi)
