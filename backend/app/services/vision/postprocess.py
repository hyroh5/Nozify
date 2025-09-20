import cv2, numpy as np

def mask_to_polygon(mask: np.ndarray, approx_eps: float=3.0):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    epsilon = approx_eps
    approx = cv2.approxPolyDP(contour, epsilon, True)
    poly = [(float(x), float(y)) for [[x,y]] in approx]
    return poly, contour
