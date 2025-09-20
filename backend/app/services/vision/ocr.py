import cv2, numpy as np, pytesseract
from typing import List, Dict, Any
from app.core.config import VisionConfig

def _preprocess(gray):
    # 대비 보정
    gray = cv2.convertScaleAbs(gray, alpha=1.3, beta=0)
    # Otsu 이진화
    blur = cv2.GaussianBlur(gray, (3,3), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    # 글자 연결
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, k, iterations=1)
    return th

def _tess(img, psm):
    langs = VisionConfig.OCR_LANGS.replace(",", "+")
    config = f"-l {langs} --oem 3 --psm {psm}"
    return pytesseract.image_to_data(img, config=config, output_type=pytesseract.Output.DICT)

def run_ocr(img_bgr, roi=None) -> List[Dict[str, Any]]:
    h, w = img_bgr.shape[:2]
    if roi:
        x,y,rw,rh = roi
        roi_img = img_bgr[y:y+rh, x:x+rw]
    else:
        x,y,rw,rh = 0,0,w,h
        roi_img = img_bgr

    gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    results = []

    for scale in (1.0, 1.5, 2.0):
        g = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        th = _preprocess(g)
        for psm in (7, 6):
            data = _tess(th, psm)
            n = len(data["text"])
            for i in range(n):
                txt = ("" if data["text"][i] is None else str(data["text"][i])).strip()
                try:
                    conf = float(data["conf"][i]) / 100.0
                except Exception:
                    conf = 0.0
                if not txt or conf < 0.55:  # 조금 올림
                    continue

                bx = int(data["left"][i] / scale); by = int(data["top"][i] / scale)
                bw2 = int(data["width"][i] / scale); bh2 = int(data["height"][i] / scale)
                bx += x; by += y
                box = {"x": bx / w, "y": by / h, "w": bw2 / w, "h": bh2 / h}
                results.append({"text": txt.upper(), "confidence": conf, "box": box})

        # 이미 충분히 텍스트가 나오면 더 안 키워도 됨
        if len(results) >= 6:
            break

    # 중복 박스/텍스트 간단 정리(같은 문자열 우선순위: 더 높은 conf)
    dedup = {}
    for r in results:
        key = (r["text"], round(r["box"]["x"],3), round(r["box"]["y"],3))
        if key not in dedup or r["confidence"] > dedup[key]["confidence"]:
            dedup[key] = r
    return list(dedup.values())
