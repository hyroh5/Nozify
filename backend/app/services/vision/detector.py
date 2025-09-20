# backend/app/services/vision/detector.py
from typing import Optional, Dict, Any
import os
import numpy as np
import cv2
import onnxruntime as ort
from ultralytics import YOLO

from app.core.config import VisionConfig
from .preprocess import letterbox
from .postprocess import mask_to_polygon
from .utils import clamp01


class BottleDetector:
    def __init__(self, model_path: str, device: str = "cpu", score_th: float = 0.5):
        self.score_th = score_th
        self.device = device
        self.session = None
        self.yolo = None
        self.model_loaded = False

        # ---- 1) PyTorch(.pt) 먼저 시도 ----
        try:
            pt_path = getattr(VisionConfig, "BOTTLE_MODEL_PT_PATH", "") or ""
            if pt_path and os.path.exists(pt_path):
                print("[BottleDetector] try PT:", os.path.abspath(pt_path))
                self.yolo = YOLO(pt_path)
                self.model_loaded = True
                print("[BottleDetector] PyTorch model loaded")
                try:
                    names = getattr(self.yolo.model, "names", None)
                    print("[BottleDetector] model.names:", names)
                except Exception as e:
                    print("[BottleDetector] names read fail:", e)
            else:
                print("[BottleDetector] PT file not found:", pt_path)
        except Exception as e:
            print("YOLO PT load fail:", e)

        # ---- 2) PT 실패/없음이면 ONNX 로드 ----
        if not self.model_loaded:
            try:
                onnx_path = model_path
                if onnx_path and os.path.exists(onnx_path):
                    providers = (
                        ["CPUExecutionProvider"]
                        if device == "cpu"
                        else ["CUDAExecutionProvider", "CPUExecutionProvider"]
                    )
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

    def detect(
        self, img_bgr, guide_box: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        h, w = img_bgr.shape[:2]

        if not self.ready():
            return {
                "present": False,
                "score": 0.0,
                "mask_polygon": None,
                "bbox": {"x": 0, "y": 0, "w": 0, "h": 0},
                "area_ratio": 0.0,
                "inside_ratio": 0.0,
            }

        # =======================
        # 1) Ultralytics PT 경로
        # =======================
        if self.yolo is not None:
            try:
                print(
                    "[det] PT predict start 640 (no class filter, conf=0.05, iou=0.45)"
                )
                # (패스1) 클래스 필터 없이 느슨하게
                res = self.yolo.predict(
                    img_bgr[:, :, ::-1],  # BGR->RGB
                    imgsz=640,
                    conf=0.05,
                    iou=0.45,
                    verbose=False,
                )[0]
                n1 = 0 if res.boxes is None else len(res.boxes)
                print(f"[det] PT predict done (pass1-640) boxes={n1}")

                # (패스2) 0개면 해상도 업
                if res.boxes is None or len(res.boxes) == 0:
                    print("[det] retry PT 960")
                    res = self.yolo.predict(
                        img_bgr[:, :, ::-1],
                        imgsz=960,  # 업샘플 효과
                        conf=0.05,
                        iou=0.45,
                        verbose=False,
                    )[0]
                    n2 = 0 if res.boxes is None else len(res.boxes)
                    print(f"[det] PT predict done (pass2-960) boxes={n2}")

                # 그래도 없으면 실패
                if res.boxes is None or len(res.boxes) == 0:
                    print("[det] PT still no boxes → present=False")
                    return {
                        "present": False,
                        "score": 0.0,
                        "mask_polygon": None,
                        "bbox": {"x": 0, "y": 0, "w": 0, "h": 0},
                        "area_ratio": 0.0,
                        "inside_ratio": 0.0,
                    }

                # 최고 conf 박스 선택
                confs = res.boxes.conf.cpu().numpy()
                idx = int(confs.argmax())
                top_conf = float(confs[idx])

                # bbox 정규화 x,y,w,h
                cx, cy, bw, bh = map(float, res.boxes.xywhn[idx].cpu().numpy())
                bx = clamp01(cx - bw / 2.0)
                by = clamp01(cy - bh / 2.0)
                bw = clamp01(bw)
                bh = clamp01(bh)
                bbox = {"x": bx, "y": by, "w": bw, "h": bh}
                print(f"[det] picked conf={top_conf:.3f}, bbox={bbox}")

                # 세그 다각형(있을 때만)
                poly = None
                if getattr(res, "masks", None) is not None and len(res.masks.xy) > idx:
                    pts = res.masks.xy[idx]  # 픽셀 좌표
                    poly = [
                        [clamp01(float(x) / w), clamp01(float(y) / h)] for x, y in pts
                    ]

                area_ratio = bw * bh
                present = top_conf >= self.score_th

                return {
                    "present": present,
                    "score": top_conf,
                    "mask_polygon": poly,
                    "bbox": bbox,
                    "area_ratio": area_ratio,
                    "inside_ratio": 1.0,
                }
            except Exception as e:
                print("PT inference error:", e)

        # =======================
        # 2) ONNX 폴백 경로
        # =======================
        try:
            img_resized, scale, dx, dy, (orig_h, orig_w) = letterbox(
                img_bgr, (640, 640)
            )
            blob = img_resized[:, :, ::-1].transpose(2, 0, 1)  # BGR->RGB, HWC->CHW
            blob = np.expand_dims(blob, 0).astype(np.float32) / 255.0
            print("[det] ONNX predict start")
            out = self.session.run(None, {"images": blob})
            print("[det] ONNX predict done")
            pred_mask = out[0][0]  # (H, W) 가정
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

        # --- 실패 시 기본 ---
        return {
            "present": False,
            "score": 0.0,
            "mask_polygon": None,
            "bbox": {"x": 0, "y": 0, "w": 0, "h": 0},
            "area_ratio": 0.0,
            "inside_ratio": 0.0,
        }


# 싱글톤 인스턴스
detector = BottleDetector(
    VisionConfig.MODEL_PATH,
    VisionConfig.DEVICE,
    VisionConfig.THRESH_BOTTLE_SCORE,
)
