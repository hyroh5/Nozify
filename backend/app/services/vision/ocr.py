# app/services/vision/ocr.py
import cv2
import numpy as np
import pytesseract
from typing import List, Dict, Any
from app.core.config import VisionConfig

try:
    # 일부 환경에선 TesseractError가 필요할 수 있음
    from pytesseract import TesseractError
except Exception:  # pragma: no cover
    TesseractError = Exception


def _preprocess(gray: np.ndarray) -> List[np.ndarray]:
    """
    입력: 그레이스케일 이미지
    출력: [정이진화, 역이진화] 두 버전 (모폴로지 후처리 포함)
    """
    # 대비 보정
    gray = cv2.convertScaleAbs(gray, alpha=1.3, beta=0)

    # 약한 노이즈 제거
    blur = cv2.GaussianBlur(gray, (3, 3), 0)

    # Otsu 이진화(정/역)
    _, th_bin = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    _, th_inv = cv2.threshold(
        blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # 글자 끊김 보완
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    th_bin = cv2.morphologyEx(th_bin, cv2.MORPH_CLOSE, k, iterations=1)
    th_inv = cv2.morphologyEx(th_inv, cv2.MORPH_CLOSE, k, iterations=1)

    return [th_bin, th_inv]


def _tess(img: np.ndarray, psm: int) -> Dict[str, List[Any]]:
    langs = VisionConfig.OCR_LANGS.replace(",", "+")
    config = f"-l {langs} --oem 3 --psm {psm}"
    return pytesseract.image_to_data(
        img, config=config, output_type=pytesseract.Output.DICT
    )


def run_ocr(img_bgr: np.ndarray, roi=None) -> List[Dict[str, Any]]:
    """
    img_bgr: 원본 BGR 이미지
    roi: (x, y, w, h) 픽셀 좌표. None이면 전체 이미지 사용
    반환: [{'text':str,'confidence':float,'box':{'x':..,'y':..,'w':..,'h':..}}, ...]
          box는 정규화 좌표(0~1)
    """
    h, w = img_bgr.shape[:2]

    # 진입 로그
    print(f"[LOG][OCR] OCR 시작, ROI={roi if roi else '전체 이미지'}")

    # ROI 잘라내기
    if roi:
        x, y, rw, rh = roi
        roi_img = img_bgr[y : y + rh, x : x + rw]
    else:
        x, y, rw, rh = 0, 0, w, h
        roi_img = img_bgr

    gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    results: List[Dict[str, Any]] = []

    # 작은 입력 대응: 더 큰 스케일까지 확대 시도
    scales = (1.0, 1.8, 2.4, 3.0)
    psms = (7, 6)  # 7: single line, 6: assume a block

    for scale in scales:
        # 확대
        g = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # 정/역 이진화 모두 시도
        for th in _preprocess(g):
            for psm in psms:
                try:
                    data = _tess(th, psm)
                except TesseractError as e:  # 안전장치
                    print("[LOG][OCR] tesseract error:", e)
                    continue

                n = len(data.get("text", []))
                for i in range(n):
                    raw_text = data["text"][i]
                    txt = ("" if raw_text is None else str(raw_text)).strip()

                    # conf 타입 안전 처리
                    try:
                        conf = float(data["conf"][i]) / 100.0
                    except Exception:
                        conf = 0.0

                    # 컷(완화): 0.45
                    if not txt or conf < 0.45:
                        continue

                    # 박스 좌표 역스케일 + 원본 좌표계 보정
                    try:
                        bx = int(data["left"][i] / scale)
                        by = int(data["top"][i] / scale)
                        bw2 = int(data["width"][i] / scale)
                        bh2 = int(data["height"][i] / scale)
                    except Exception:
                        continue

                    bx += x
                    by += y

                    box = {
                        "x": bx / w,
                        "y": by / h,
                        "w": bw2 / w,
                        "h": bh2 / h,
                    }
                    results.append(
                        {"text": txt.upper(), "confidence": conf, "box": box}
                    )

        # 충분히 텍스트가 모이면 조기종료
        if len(results) >= 6:
            break

    # 간단 중복 제거: (텍스트, 대략 좌표) 키로 최고 conf만 유지
    dedup: Dict[Any, Dict[str, Any]] = {}
    for r in results:
        key = (r["text"], round(r["box"]["x"], 3), round(r["box"]["y"], 3))
        if key not in dedup or r["confidence"] > dedup[key]["confidence"]:
            dedup[key] = r

    texts = list(dedup.values())
    # texts = list(dedup.values()) 바로 다음에 추가
    clean = []
    for r in texts:
        t = r["text"]
        conf = r["confidence"]
        # 전각/기호/한 글자 위주 제거
        if conf < 0.60:
            continue
        if len(t) <= 1 and t not in {"°"}:
            continue
        if all(ch in "|/\\{}[]()-_=+:.!~" for ch in t):
            continue
        clean.append(r)
    texts = clean


    # 반환 로그
    print(f"[LOG][OCR] OCR 결과: {texts}")

    return texts
