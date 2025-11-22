from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from app.core.db import get_db
from app.models.wishlist import Wishlist
from app.models.perfume import Perfume
from app.models.user import User
from app.models.base import uuid_hex_to_bytes, uuid_bytes_to_hex
from app.api.deps import get_current_user_id
from datetime import datetime

router = APIRouter(tags=["User"])

def _serialize_perfume_for_wishlist(w: Wishlist):
    """Wishlist 항목을 직렬화하며 Perfume 정보를 포함합니다."""
    p = w.perfume
    if not p:
        return None
        
    return {
        "added_at": w.created_at.isoformat() if w.created_at else None,
        "perfume": {
            "id": uuid_bytes_to_hex(p.id),
            "name": p.name,
            "brand_name": p.brand_name,
            "image_url": p.image_url,
            "gender": p.gender,
        }
    }

@router.get("/wishlist")
def get_wishlist(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uid: User = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if uid is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required for this endpoint")

    user_id_to_filter = uid.id 

    rows = (
        db.query(Wishlist)
        .options(joinedload(Wishlist.perfume))
        .filter(Wishlist.user_id == user_id_to_filter)
        .order_by(Wishlist.created_at.desc())
        .offset(offset).limit(limit).all()
    )
    
    results = [w for w in [_serialize_perfume_for_wishlist(r) for r in rows] if w is not None]
    return results

@router.post("/wishlist")
def add_wishlist(
    perfume_id: str,
    uid: User = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if uid is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required for this endpoint")

    try:
        pid = uuid_hex_to_bytes(perfume_id)
    except Exception:
        raise HTTPException(400, "invalid perfume_id (hex uuid)")

    p = db.get(Perfume, pid)
    if not p:
        raise HTTPException(404, "perfume not found")
        
    user_id_to_filter = uid.id 

    exists = (
        db.query(Wishlist)
        .filter(Wishlist.user_id == user_id_to_filter, Wishlist.perfume_id == pid)
        .first()
    )
    if exists:
        return {"ok": True, "duplicated": True}

    row = Wishlist(user_id=user_id_to_filter, perfume_id=pid)
    db.add(row)
    db.commit()
    return {"ok": True}

@router.delete("/wishlist/{perfume_id}")
def remove_wishlist(
    perfume_id: str,
    uid: User = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if uid is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required for this endpoint")

    try:
        pid = uuid_hex_to_bytes(perfume_id)
    except Exception:
        raise HTTPException(400, "invalid perfume_id (hex uuid)")

    user_id_to_filter = uid.id 

    row = (
        db.query(Wishlist)
        .filter(Wishlist.user_id == user_id_to_filter, Wishlist.perfume_id == pid)
        .first()
    )
    if not row:
        return {"ok": True, "deleted": 0}

    db.delete(row)
    db.commit()
    return {"ok": True, "deleted": 1}