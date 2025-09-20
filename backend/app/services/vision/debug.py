import cv2, os
from app.core.config import VisionConfig

def save_overlay(img, bbox, poly, request_id):
    dbg = img.copy()
    h,w=img.shape[:2]
    if poly:
        pts=[(int(x*w),int(y*h)) for x,y in poly]
        cv2.polylines(dbg,[np.array(pts,np.int32)],True,(0,255,0),2)
    if bbox:
        bx=int(bbox["x"]*w);by=int(bbox["y"]*h)
        bw=int(bbox["w"]*w);bh=int(bbox["h"]*h)
        cv2.rectangle(dbg,(bx,by),(bx+bw,by+bh),(255,0,0),2)
    os.makedirs(VisionConfig.DEBUG_DIR,exist_ok=True)
    path=os.path.join(VisionConfig.DEBUG_DIR,f"{request_id}_overlay.jpg")
    cv2.imwrite(path,dbg)
    return path
