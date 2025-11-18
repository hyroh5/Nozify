import cv2, numpy as np, pytesseract, math
from typing import List, Dict, Any, Iterable
from app.core.config import VisionConfig


def _clahe(gray: np.ndarray) -> np.ndarray:
    # 색 유리/반사 환경 대비 향상
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def _preprocess_variants(gray: np.ndarray) -> Iterable[np.ndarray]:
    """한 장의 회전된 그레이 이미지를 받아 여러 이진화 버전을 생성."""
    g = cv2.GaussianBlur(gray, (3, 3), 0)

    # Otsu (정/역)
    _, th_bin = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    _, th_inv = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 적응형 (조명 편차 대응)
    at = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                            cv2.THRESH_BINARY, 31, 9)
    at_inv = cv2.bitwise_not(at)

    k = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    yield cv2.morphologyEx(th_bin, cv2.MORPH_CLOSE, k, iterations=1)
    yield cv2.morphologyEx(th_inv, cv2.MORPH_CLOSE, k, iterations=1)
    yield cv2.morphologyEx(at,     cv2.MORPH_CLOSE, k, iterations=1)
    yield cv2.morphologyEx(at_inv, cv2.MORPH_CLOSE, k, iterations=1)


def _tess(img: np.ndarray, psm: int) -> Dict[str, List]:
    langs = VisionConfig.OCR_LANGS.replace(",", "+")
    # psm 11: 희소 텍스트(여러 줄), 6: 균일한 블럭, 7: 한 줄
    config = f"-l {langs} --oem 3 --psm {psm}"
    return pytesseract.image_to_data(
        img, config=config, output_type=pytesseract.Output.DICT
    )


def _rotate_bound(image: np.ndarray, angle: float) -> np.ndarray:
    """캔버스를 늘려 잘림 없이 회전."""
    (h, w) = image.shape[:2]
    cX, cY = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D((cX, cY), angle, 1.0)
    cos, sin = (abs(M[0, 0]), abs(M[0, 1]))
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY
    return cv2.warpAffine(image, M, (nW, nH), flags=cv2.INTER_CUBIC,
                        borderMode=cv2.BORDER_REPLICATE)


def _is_symbolic(s: str) -> bool:
    # 기호만/숫자 1자 같은 노이즈 억제
    s = s.strip()
    if not s: return True
    letters = sum(ch.isalpha() for ch in s)
    digits  = sum(ch.isdigit() for ch in s)
    return (letters + digits) == 0 or len(s) == 1 and not s.isalpha()


def run_ocr(img_bgr, roi=None) -> List[Dict[str, Any]]:
    h, w = img_bgr.shape[:2]
    print(f"[LOG][OCR] OCR 시작, ROI={roi if roi else '전체 이미지'}")

    if roi:
        x, y, rw, rh = roi
        crop = img_bgr[y:y + rh, x:x + rw]
    else:
        x, y, rw, rh = 0, 0, w, h
        crop = img_bgr

    gray0 = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray0 = _clahe(gray0)

    results: List[Dict[str, Any]] = []

    # 회전 스윕(기울어진 라벨 대응)
    angles = (-25, -18, -12, -8, -5, 0, 5, 8, 12, 18, 25)
    # 확대 스케일
    scales = (1.0, 1.6, 2.2, 2.8)

    for ang in angles:
        g_rot = _rotate_bound(gray0, ang)
        for scale in scales:
            g = cv2.resize(g_rot, None, fx=scale, fy=scale,
                        interpolation=cv2.INTER_CUBIC)

            for th in _preprocess_variants(g):
                for psm in (11, 7, 6):
                    data = _tess(th, psm)
                    n = len(data["text"])
                    for i in range(n):
                        raw = data["text"][i]
                        if raw is None: 
                            continue
                        txt = str(raw).strip()
                        try:
                            conf = float(data["conf"][i]) / 100.0
                        except Exception:
                            conf = 0.0

                        if conf < 0.55 or _is_symbolic(txt):
                            continue

                        # 회전/스케일 역투영(여기서는 크기/위치 대략만)
                        bx = int(data["left"][i] / scale)
                        by = int(data["top"][i] / scale)
                        bw2 = int(data["width"][i] / scale)
                        bh2 = int(data["height"][i] / scale)

                        # 회전으로 바뀐 좌표계를 원본 ROI 기준으로 보정: 
                        # 간단하게 bounding box 중심만 복원해도 충분
                        # (정밀한 어핀 역변환은 성능 이득 미미)
                        bx += x; by += y
                        box = {"x": bx / w, "y": by / h, "w": bw2 / w, "h": bh2 / h}

                        results.append({
                            "text": txt.upper(),
                            "confidence": conf,
                            "box": box
                        })

                # 충분히 나왔으면 조기 종료
                if len(results) >= 12:
                    break
            if len(results) >= 12:
                break
        if len(results) >= 12:
            break

        

    # 중복 정리: (문자열, 좌상단 라운드 좌표) 기준으로 conf 높은 것만
    dedup = {}
    for r in results:
        key = (r["text"], round(r["box"]["x"], 3), round(r["box"]["y"], 3))
        if key not in dedup or r["confidence"] > dedup[key]["confidence"]:
            dedup[key] = r

    texts = list(dedup.values())
    print(f"[LOG][OCR] OCR 결과: {texts}")
    return texts

# --- NEW: 회전 OCR ---
def run_ocr_rotated(img_bgr, roi=None, angles=None):
    if angles is None:
        angles = [-18,-12,-9,-6,-3,0,3,6,9,12,18]

    h0, w0 = img_bgr.shape[:2]
    if roi:
        x, y, rw, rh = roi
        crop = img_bgr[y:y+rh, x:x+rw]
    else:
        x, y, rw, rh = 0, 0, w0, h0
        crop = img_bgr

    best = {"score": -1e9, "texts": []}

    # 간단 키워드(보너스)
    KEYWORDS = {"EAU", "PARFUM", "PARFUME", "CHANEL", "ALL", "OF", "ME", "NARCISO", "RODRIGUEZ", "N°", "NO", "Nº"}

    for ang in angles:
        # 회전 행렬
        h, w = crop.shape[:2]
        cx, cy = w/2.0, h/2.0
        M = cv2.getRotationMatrix2D((cx, cy), ang, 1.0)
        rot = cv2.warpAffine(crop, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

        # 기존 run_ocr 파이프라인 재사용(roi=None로 전체 rot 사용)
        toks = run_ocr(rot, roi=None)

        # 점수 함수
        if toks:
            confs = [t["confidence"] for t in toks]
            hi = sum(c >= 0.80 for c in confs)
            mean_c = float(np.mean(confs))
            bonus = 0.0
            for t in toks:
                if any(k in t["text"] for k in KEYWORDS):
                    bonus += 0.2
            score = hi + 0.5*mean_c + bonus
        else:
            score = -1

        if score > best["score"]:
            # 박스 좌표 원복(회전 역변환 + 원본 오프셋)
            M_inv = cv2.invertAffineTransform(M)
            restored = []
            for t in toks:
                bx = t["box"]
                # rot 좌표계(정규화) -> rot 픽셀
                px = bx["x"] * w; py = bx["y"] * h
                pw = bx["w"] * w; ph = bx["h"] * h
                # 좌상/우하 2점만 역투영 후 bbox 재구성
                p1 = np.dot(M_inv, np.array([px, py, 1.0]))
                p2 = np.dot(M_inv, np.array([px+pw, py+ph, 1.0]))
                rx0, ry0 = p1[0], p1[1]
                rx1, ry1 = p2[0], p2[1]
                # 원본 전체 이미지 기준 정규화
                ox0 = (rx0 + x) / w0; oy0 = (ry0 + y) / h0
                ow  = max(1.0, (rx1 - rx0)) / w0
                oh  = max(1.0, (ry1 - ry0)) / h0
                restored.append({
                    "text": t["text"],
                    "confidence": t["confidence"],
                    "box": {"x": clamp01(ox0), "y": clamp01(oy0), "w": clamp01(ow), "h": clamp01(oh)}
                })
            best = {"score": score, "texts": restored}

    return best["texts"]
