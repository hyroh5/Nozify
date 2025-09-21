import cv2, numpy as np

def calc_quality(img_bgr):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.Laplacian(gray, cv2.CV_64F).var()
    brightness = float(np.mean(gray)/255.0)
    # glare: 밝은 픽셀 비율
    glare_ratio = float(np.sum(gray>240)/(gray.size))
    print(f"[LOG][QUALITY] blur={blur:.2f}, brightness={brightness:.3f}, glare={glare_ratio:.3f}")
    return {"blur": blur, "brightness": brightness, "glare_ratio": glare_ratio}
