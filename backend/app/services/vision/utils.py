# backend/app/services/vision/utils.py
import numpy as np
from typing import Tuple


def _load_cv2():
    try:
        import cv2
        return cv2
    except Exception as e:
        raise RuntimeError(f"OpenCV load failed: {e}")


def decode_image(file_bytes: bytes) -> Tuple[np.ndarray, int, int]:
    cv2 = _load_cv2()

    arr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("INVALID_FILE")

    h, w = img.shape[:2]
    return img, w, h


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))
