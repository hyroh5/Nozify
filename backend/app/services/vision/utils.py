import cv2, numpy as np
from typing import Tuple


def decode_image(file_bytes: bytes) -> Tuple[np.ndarray, int, int]:
    arr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)  # BGR
    if img is None:
        raise ValueError("INVALID_FILE")
    h, w = img.shape[:2]
    return img, w, h


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))
