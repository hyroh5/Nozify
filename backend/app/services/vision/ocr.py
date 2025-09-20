import cv2, numpy as np, pytesseract
from typing import List, Dict, Any
from app.core.config import VisionConfig


def run_ocr(img_bgr: np.ndarray, roi=None) -> List[Dict[str, Any]]:
    """
    ROI: (x,y,w,h) 픽셀 좌표 튜플. None이면 전체 이미지.
    반환: [{'text':str,'confidence':float,'box':{'x':..,'y':..,'w':..,'h':..}}]
    """
    h, w = img_bgr.shape[:2]
    if roi:
        x, y, rw, rh = roi
        roi_img = img_bgr[y : y + rh, x : x + rw]
    else:
        x, y, rw, rh = 0, 0, w, h
        roi_img = img_bgr

    gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)

    # 대비/밝기 강화
    gray = cv2.convertScaleAbs(gray, alpha=2.0, beta=30)

    # 미세 노이즈 억제
    gray = cv2.bilateralFilter(gray, d=5, sigmaColor=50, sigmaSpace=50)

    # 탑햇으로 밝은 글자 강조
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)

    # 약한 블러로 노이즈 억제
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    # Otsu 이진화
    _, gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    langs = VisionConfig.OCR_LANGS.replace(",", "+")
    config = f"-l {langs} --oem 3 --psm 6"

    try:
        data = pytesseract.image_to_data(
            gray, config=config, output_type=pytesseract.Output.DICT
        )
    except TesseractError as e:
        print("tesseract error:", e)
        return []

    results = []
    n = len(data["text"])
    for i in range(n):
        # 1) 텍스트 안전 처리
        raw_text = data["text"][i]
        txt = ("" if raw_text is None else str(raw_text)).strip()
        # 2) 신뢰도 타입 안전 처리 (int/float/str 모두 대응)
        raw_conf = data["conf"][i]
        try:
            conf = float(raw_conf) / 100.0
        except Exception:
            conf = 0.0

        if not txt or conf < 0.3:
            continue

        # 3) 박스 좌표도 타입 캐스팅
        bx = int(data["left"][i])
        by = int(data["top"][i])
        bw = int(data["width"][i])
        bh = int(data["height"][i])

        # ROI 원본 좌표계로 보정
        bx += x
        by += y
        box = {"x": bx / w, "y": by / h, "w": bw / w, "h": bh / h}

        results.append({"text": txt.upper(), "confidence": conf, "box": box})

    return results
