from __future__ import annotations
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.wishlist import Wishlist
from app.models.perfume import Perfume
from app.models.base import uuid_hex_to_bytes, uuid_bytes_to_hex

router = APIRouter(prefix="/me", tags=["Me"])

def _require_user(x_user_id: str | None) -> bytes:
    if not x_user_id:
        raise HTTPException(401, "X-User-Id header required (hex uuid)")
    try:
        return uuid_hex_to_bytes(x_user_id)
    except Exception:
        raise HTTPException(400, "invalid X-User-Id (hex uuid)")

def _ser_perfume(p: Perfume):
    return {
        "id": uuid_bytes_to_hex(p.id),
        "name": p.name,
        "brand_name": p.brand_name,
        "image_url": p.image_url,
        "gender": p.gender,
    }

@router.get("/wishlist")
def get_wishlist(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    uid = _require_user(x_user_id)
    rows = (
        db.query(Wishlist)
          .filter(Wishlist.user_id == uid)
          .order_by(Wishlist.created_at.desc())
          .offset(offset).limit(limit).all()
    )
    return [_ser_perfume(w.perfume) for w in rows]

@router.post("/wishlist")
def add_wishlist(
    perfume_id: str,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    uid = _require_user(x_user_id)
    try:
        pid = uuid_hex_to_bytes(perfume_id)
    except Exception:
        raise HTTPException(400, "invalid perfume_id (hex uuid)")

    p = db.get(Perfume, pid)
    if not p:
        raise HTTPException(404, "perfume not found")

    exists = (
        db.query(Wishlist)
          .filter(Wishlist.user_id == uid, Wishlist.perfume_id == pid)
          .first()
    )
    if exists:
        return {"ok": True, "duplicated": True}

    w = Wishlist(user_id=uid, perfume_id=pid)
    db.add(w)
    db.commit()
    return {"ok": True}

@router.delete("/wishlist/{perfume_id}")
def remove_wishlist(
    perfume_id: str,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    uid = _require_user(x_user_id)
    try:
        pid = uuid_hex_to_bytes(perfume_id)
    except Exception:
        raise HTTPException(400, "invalid perfume_id (hex uuid)")

    deleted = (
        db.query(Wishlist)
          .filter(Wishlist.user_id == uid, Wishlist.perfume_id == pid)
          .delete()
    )
    db.commit()
    return {"ok": True, "deleted": deleted > 0}
