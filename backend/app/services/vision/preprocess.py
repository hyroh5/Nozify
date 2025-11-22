# backend/app/services/vision/preprocess.py
import numpy as np
from .utils import _load_cv2


def letterbox(img, new_shape=(640, 640), color=(114, 114, 114)):
    cv2 = _load_cv2()

    h, w = img.shape[:2]
    scale = min(new_shape[0] / h, new_shape[1] / w)
    nh, nw = int(h * scale), int(w * scale)

    img_resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)

    top = (new_shape[0] - nh) // 2
    left = (new_shape[1] - nw) // 2

    canvas = np.full((new_shape[0], new_shape[1], 3), color, dtype=np.uint8)
    canvas[top:top + nh, left:left + nw] = img_resized

    return canvas, scale, left, top, (h, w)
