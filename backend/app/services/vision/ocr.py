# backend/app/services/vision/ocr.py
from typing import List, Dict, Any, Optional, Union
import numpy as np
import pytesseract
from pytesseract import Output

from .utils import _load_cv2
from app.core.config import VisionConfig  # 지금은 안 쓰지만 남겨둬도 무방


def _parse_roi(
    roi: Union[Dict[str, float], List[float], tuple, None],
    w: int,
    h: int,
) -> Optional[Dict[str, int]]:
    """
    roi 를 실제 픽셀 좌표로 변환
    - dict 타입은 정규화 좌표 x, y, w, h 로 간주
    - list, tuple 타입은 이미 픽셀 단위로 들어온 것으로 간주
    """
    if roi is None:
        return None

    # dict 타입  정규화 좌표로 간주
    if isinstance(roi, dict):
        x_norm = float(roi.get("x", 0.0))
        y_norm = float(roi.get("y", 0.0))
        w_norm = float(roi.get("w", 1.0))
        h_norm = float(roi.get("h", 1.0))

        x = int(x_norm * w)
        y = int(y_norm * h)
        rw = int(w_norm * w)
        rh = int(h_norm * h)

    # list, tuple 타입  픽셀 좌표로 간주
    elif isinstance(roi, (list, tuple)) and len(roi) == 4:
        x = int(roi[0])
        y = int(roi[1])
        rw = int(roi[2])
        rh = int(roi[3])

    else:
        return None

    # 이미지 경계 안으로 클램프
    x = max(0, min(x, w - 1))
    y = max(0, min(y, h - 1))
    rw = max(1, min(rw, w - x))
    rh = max(1, min(rh, h - y))

    return {"x": x, "y": y, "w": rw, "h": rh}


def _process_ocr_result(result, w, h, x_offset, y_offset) -> List[Dict[str, Any]]:
    """
    PaddleOCR 결과 파서였던 함수.
    지금은 안 쓰지만, 혹시 나중에 폴리곤 박스 포맷을 재활용할 일이 있을 수 있어 남겨둠.
    """
    texts: List[Dict[str, Any]] = []

    if not result:
        return texts

    lines = []
    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
        lines = result[0]
    else:
        lines = result

    for line in lines:
        try:
            box, (txt, score) = line
        except Exception:
            continue

        box = np.array(box, dtype=np.float32)
        xs = (box[:, 0] + x_offset) / w
        ys = (box[:, 1] + y_offset) / h

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


def _apply_clahe(crop_img):
    """CLAHE 대비 보정 전처리 적용"""
    cv2 = _load_cv2()
    if crop_img is None or crop_img.size == 0:
        return None

    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    try:
        # CLAHE (Adaptive Histogram Equalization) 적용
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_gray = clahe.apply(gray)
    except Exception:
        enhanced_gray = gray

    return cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2BGR)


def _tesseract_data_to_texts(
    data: Dict[str, Any],
    img_w: int,
    img_h: int,
    x_offset: int,
    y_offset: int,
) -> List[Dict[str, Any]]:
    """
    pytesseract.image_to_data 결과(DICT)를
    Nozify에서 사용하는 텍스트 리스트 포맷으로 변환
    """
    texts: List[Dict[str, Any]] = []

    n = len(data.get("text", []))
    for i in range(n):
        txt = data["text"][i].strip() if data["text"][i] is not None else ""
        # conf는 문자열로 들어옴
        try:
            conf = float(data["conf"][i])
        except Exception:
            conf = -1.0

        # 내용이 없거나 confidence가 -1이면 스킵
        if not txt or conf < 0:
            continue

        left = int(data["left"][i])
        top = int(data["top"][i])
        width = int(data["width"][i])
        height = int(data["height"][i])

        # 원본 이미지 기준 절대 좌표
        x1_abs = left + x_offset
        y1_abs = top + y_offset

        # 정규화 좌표
        bx = float(x1_abs) / float(img_w)
        by = float(y1_abs) / float(img_h)
        bw = float(width) / float(img_w)
        bh = float(height) / float(img_h)

        texts.append(
            {
                "text": txt,
                "confidence": conf / 100.0,  # 0~100 → 0~1 스케일로 변환
                "box": {"x": bx, "y": by, "w": bw, "h": bh},
            }
        )

    return texts


def run_ocr(
    img_bgr,
    roi: Optional[Union[Dict[str, float], List[float], tuple]] = None,
) -> List[Dict[str, Any]]:
    """
    기본 방향 텍스트에 대한 OCR.
    PaddleOCR 대신 pytesseract.image_to_data 사용.
    """
    cv2 = _load_cv2()
    h, w = img_bgr.shape[:2]

    roi_px = _parse_roi(roi, w, h) if roi is not None else None
    if roi_px is not None:
        x, y = roi_px["x"], roi_px["y"]
        rw, rh = roi_px["w"], roi_px["h"]
        crop = img_bgr[y : y + rh, x : x + rw]
    else:
        x, y = 0, 0
        crop = img_bgr

    # 대비 보정
    img_ocr_input = _apply_clahe(crop)
    if img_ocr_input is None:
        return []

    # pytesseract는 RGB 기준이라 BGR → RGB 변환
    img_rgb = cv2.cvtColor(img_ocr_input, cv2.COLOR_BGR2RGB)

    # pytesseract 결과를 DICT 형태로 받음
    data = pytesseract.image_to_data(img_rgb, output_type=Output.DICT)

    texts = _tesseract_data_to_texts(
        data=data,
        img_w=w,
        img_h=h,
        x_offset=x,
        y_offset=y,
    )

    return texts


def run_ocr_rotated(
    img_bgr,
    roi: Optional[Union[Dict[str, float], List[float], tuple]] = None,
) -> List[Dict[str, Any]]:
    """
    이미지 90도 회전 후 OCR을 실행하여 누워있는 텍스트 인식률 보강.
    PaddleOCR 대신 pytesseract.image_to_data 사용.
    """
    cv2 = _load_cv2()
    h, w = img_bgr.shape[:2]

    # 1. ROI 크롭
    roi_px = _parse_roi(roi, w, h) if roi is not None else None
    if roi_px is not None:
        x, y = roi_px["x"], roi_px["y"]
        rw, rh = roi_px["w"], roi_px["h"]
        crop = img_bgr[y : y + rh, x : x + rw]
    else:
        x, y = 0, 0
        crop = img_bgr

    if crop.size == 0:
        return []

    # 2. 90도 시계방향 회전 이미지 생성
    crop_90 = cv2.rotate(crop, cv2.ROTATE_90_CLOCKWISE)

    # 3. 전처리 적용
    img_ocr_input_90 = _apply_clahe(crop_90)
    if img_ocr_input_90 is None:
        return []

    # BGR → RGB
    img_rgb_90 = cv2.cvtColor(img_ocr_input_90, cv2.COLOR_BGR2RGB)

    # 4. OCR 실행
    data_90 = pytesseract.image_to_data(img_rgb_90, output_type=Output.DICT)

    texts_90: List[Dict[str, Any]] = []

    h_rot, w_rot = crop_90.shape[:2]

    n = len(data_90.get("text", []))
    for i in range(n):
        txt = data_90["text"][i].strip() if data_90["text"][i] is not None else ""
        try:
            conf = float(data_90["conf"][i])
        except Exception:
            conf = -1.0

        if not txt or conf < 0:
            continue

        left = int(data_90["left"][i])
        top = int(data_90["top"][i])
        width_box = int(data_90["width"][i])
        height_box = int(data_90["height"][i])

        # 회전된 좌표계에서 사각형 네 꼭짓점
        box_rot = np.array(
            [
                [left, top],
                [left + width_box, top],
                [left + width_box, top + height_box],
                [left, top + height_box],
            ],
            dtype=np.float32,
        )

        # 90도 시계방향 회전 → 원본 crop 좌표계로 변환
        xs_rot = box_rot[:, 0]
        ys_rot = box_rot[:, 1]

        x_orig_crop = ys_rot
        y_orig_crop = w_rot - xs_rot

        # 원본 이미지 정규화 좌표
        xs = (x_orig_crop + x) / float(w)
        ys = (y_orig_crop + y) / float(h)

        bx = float(xs.min())
        by = float(ys.min())
        bw = float(xs.max() - xs.min())
        bh = float(ys.max() - ys.min())

        texts_90.append(
            {
                "text": txt,
                "confidence": conf / 100.0,
                "box": {"x": bx, "y": by, "w": bw, "h": bh},
            }
        )

    return texts_90
