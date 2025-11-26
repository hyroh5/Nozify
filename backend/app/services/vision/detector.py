# backend/app/services/vision/detector.py
from typing import Optional, Dict, Any
import os
import numpy as np
import onnxruntime as ort

from app.core.config import VisionConfig
from .preprocess import letterbox
from .postprocess import mask_to_polygon
from .utils import clamp01, _load_cv2


class BottleDetector:
    def __init__(self, model_path: str, device: str = "cpu", score_th: float = 0.5):
        self.score_th = score_th
        self.device = device
        self.session = None
        self.yolo = None
        self.model_loaded = False

        # 1 PT 시도 ultralytics 자체를 여기서만 import
        try:
            pt_path = getattr(VisionConfig, "BOTTLE_MODEL_PT_PATH", "") or ""
            if pt_path and os.path.exists(pt_path):
                print("[BottleDetector] try PT:", os.path.abspath(pt_path))

                try:
                    from ultralytics import YOLO  # 여기서만 import
                except Exception as e:
                    print("[BottleDetector] ultralytics import fail, skip PT:", e)
                    YOLO = None

                if YOLO is not None:
                    self.yolo = YOLO(pt_path)
                    self.model_loaded = True
                    try:
                        print("[BottleDetector] model.names:", getattr(self.yolo.model, "names", None))
                    except Exception:
                        pass
                    print("[BottleDetector] PyTorch model loaded")
            else:
                print("[BottleDetector] PT file not found:", pt_path)
        except Exception as e:
            print("YOLO PT load fail:", e)

        # 2 PT 실패면 ONNX 로드
        if not self.model_loaded:
            try:
                onnx_path = model_path
                if onnx_path and os.path.exists(onnx_path):
                    providers = ["CPUExecutionProvider"] if device == "cpu" else ["CUDAExecutionProvider", "CPUExecutionProvider"]
                    print("[BottleDetector] try ONNX:", os.path.abspath(onnx_path))
                    self.session = ort.InferenceSession(onnx_path, providers=providers)
                    self.model_loaded = True
                    print("[BottleDetector] ONNX model loaded")
                else:
                    print("[BottleDetector] ONNX file not found:", onnx_path)
            except Exception as e:
                print("ONNX load fail:", e)

    def ready(self) -> bool:
        return self.model_loaded

    def detect(self, img_bgr, guide_box: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        h, w = img_bgr.shape[:2]
        print(f"[LOG][DETECT] 입력 이미지 크기: {img_bgr.shape}")

        if not self.ready():
            return {
                "present": False,
                "score": 0.0,
                "mask_polygon": None,
                "bbox": {"x": 0, "y": 0, "w": 0, "h": 0},
                "area_ratio": 0.0,
                "inside_ratio": 0.0,
            }

        # PT 경로
        if self.yolo is not None:
            try:
                imgsz_primary = 640
                imgsz_retry = 960
                if min(h, w) < 320:
                    imgsz_retry = 1280

                def run_pt(imgsz, classes=None, conf=0.05):
                    return self.yolo.predict(
                        img_bgr[:, :, ::-1],
                        imgsz=imgsz,
                        conf=conf,
                        iou=0.45,
                        classes=classes,
                        agnostic_nms=True,
                        verbose=False,
                    )[0]

                res = run_pt(imgsz_primary, classes=[39])
                if res.boxes is None or len(res.boxes) == 0:
                    res = run_pt(imgsz_retry, classes=[39, 40, 41, 75])
                if res.boxes is None or len(res.boxes) == 0:
                    res = run_pt(imgsz_retry, classes=None, conf=0.03)

                if res.boxes is None or len(res.boxes) == 0:
                    return {
                        "present": False,
                        "score": 0.0,
                        "mask_polygon": None,
                        "bbox": {"x": 0, "y": 0, "w": 0, "h": 0},
                        "area_ratio": 0.0,
                        "inside_ratio": 0.0,
                    }

                confs = res.boxes.conf.cpu().numpy()
                xywhn = res.boxes.xywhn.cpu().numpy()

                def ok_box(bw, bh, cy):
                    area = bw * bh
                    ar = (bh + 1e-6) / (bw + 1e-6)
                    return (area >= 0.002) and (ar >= 0.2) and (0.03 <= cy <= 0.97)

                cand = [i for i, (cx, cy, bw, bh) in enumerate(xywhn) if ok_box(bw, bh, cy)]
                best = max(cand, key=lambda i: confs[i]) if cand else int(confs.argmax())

                top_conf = float(confs[best])
                cx, cy, bw, bh = map(float, xywhn[best])
                bx = clamp01(cx - bw / 2)
                by = clamp01(cy - bh / 2)
                bw = clamp01(bw)
                bh = clamp01(bh)
                bbox = {"x": bx, "y": by, "w": bw, "h": bh}

                # bbox 검증: 너무 얇거나, 너무 작으면 실패로 처리
                area_ratio = bbox["w"] * bbox["h"]
                ar = (bbox["h"] + 1e-6) / (bbox["w"] + 1e-6)
                if area_ratio < 0.02 or bbox["h"] < 0.1 or ar < 0.3:
                    print(
                        f"[LOG][DETECT][PT] invalid bbox -> area_ratio={area_ratio:.4f}, "
                        f"h={bbox['h']:.3f}, ar={ar:.3f}"
                    )
                    return {
                        "present": False,
                        "score": 0.0,
                        "mask_polygon": None,
                        "bbox": {"x": 0, "y": 0, "w": 0, "h": 0},
                        "area_ratio": 0.0,
                        "inside_ratio": 0.0,
                    }

                poly = None
                if getattr(res, "masks", None) is not None and len(res.masks.xy) > best:
                    pts = res.masks.xy[best]
                    poly = [[clamp01(float(x) / w), clamp01(float(y) / h)] for x, y in pts]

                return {
                    "present": top_conf >= self.score_th,
                    "score": top_conf,
                    "mask_polygon": poly,
                    "bbox": bbox,
                    "area_ratio": float(area_ratio),
                    "inside_ratio": 1.0,
                }
            except Exception as e:
                print("PT inference error:", e)

        # ONNX 폴백
        try:
            cv2 = _load_cv2()

            img_resized, scale, dx, dy, (orig_h, orig_w) = letterbox(img_bgr, (640, 640))
            blob = img_resized[:, :, ::-1].transpose(2, 0, 1)
            blob = np.expand_dims(blob, 0).astype(np.float32) / 255.0
            out = self.session.run(None, {"images": blob})
            pred_mask = out[0][0]
            mask_bin = (pred_mask > 0.5).astype(np.uint8) * 255

            poly, contour = mask_to_polygon(mask_bin)
            if poly is None:
                return {
                    "present": False,
                    "score": 0.0,
                    "mask_polygon": None,
                    "bbox": {"x": 0, "y": 0, "w": 0, "h": 0},
                    "area_ratio": 0.0,
                    "inside_ratio": 0.0,
                }

            x, y, bw, bh = cv2.boundingRect(contour)

            def unletterbox(px, py):
                ox = (px - dx) / scale
                oy = (py - dy) / scale
                ox = max(0.0, min(float(ox), float(orig_w - 1)))
                oy = max(0.0, min(float(oy), float(orig_h - 1)))
                return ox, oy

            x0, y0 = unletterbox(x, y)
            x1, y1 = unletterbox(x + bw, y + bh)
            nbx = x0 / orig_w
            nby = y0 / orig_h
            nbw = (x1 - x0) / orig_w
            nbh = (y1 - y0) / orig_h
            bbox = {
                "x": clamp01(nbx),
                "y": clamp01(nby),
                "w": clamp01(nbw),
                "h": clamp01(nbh),
            }

            npoly = []
            for px, py in poly:
                ox, oy = unletterbox(px, py)
                npoly.append([clamp01(ox / orig_w), clamp01(oy / orig_h)])

            area_ratio = bbox["w"] * bbox["h"]
            ar = (bbox["h"] + 1e-6) / (bbox["w"] + 1e-6)

            # 여기서도 bbox 검증
            if area_ratio < 0.02 or bbox["h"] < 0.1 or ar < 0.3:
                print(
                    f"[LOG][DETECT][ONNX] invalid bbox -> area_ratio={area_ratio:.4f}, "
                    f"h={bbox['h']:.3f}, ar={ar:.3f}"
                )
                return {
                    "present": False,
                    "score": 0.0,
                    "mask_polygon": None,
                    "bbox": {"x": 0, "y": 0, "w": 0, "h": 0},
                    "area_ratio": 0.0,
                    "inside_ratio": 0.0,
                }

            return {
                "present": True,
                "score": 1.0,
                "mask_polygon": npoly,
                "bbox": bbox,
                "area_ratio": float(area_ratio),
                "inside_ratio": 1.0,
            }
        except Exception as e:
            print("ONNX inference error:", e)

        return {
            "present": False,
            "score": 0.0,
            "mask_polygon": None,
            "bbox": {"x": 0, "y": 0, "w": 0, "h": 0},
            "area_ratio": 0.0,
            "inside_ratio": 0.0,
        }



from functools import lru_cache
from pathlib import Path


def _resolve(p: str | None) -> str:
    if not p:
        return ""
    path = Path(p)
    return str(path if path.is_absolute() else (Path(__file__).resolve().parents[3] / p).resolve())


@lru_cache(maxsize=1)
def get_detector() -> BottleDetector:
    return BottleDetector(
        model_path=_resolve(getattr(VisionConfig, "MODEL_PATH", "")),
        device=getattr(VisionConfig, "DEVICE", "cpu"),
        score_th=getattr(VisionConfig, "THRESH_BOTTLE_SCORE", 0.5),
    )
