# backend/app/api/routes/user/wishlist.py
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.base import uuid_hex_to_bytes
from app.models.wishlist import Wishlist
from app.models.perfume import Perfume

router = APIRouter(tags=["User"])

# 공통: X-User-Id 헤더는 32자리 hex UUID
def _require_user_id(x_user_id: str | None) -> bytes:
    if not x_user_id:
        raise HTTPException(401, "missing X-User-Id")
    try:
        return uuid_hex_to_bytes(x_user_id)
    except Exception:
        raise HTTPException(400, "invalid X-User-Id (hex uuid)")

@router.get("/wishlist")
def list_wishlist(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    uid = _require_user_id(x_user_id)
    rows = (
        db.query(Wishlist)
          .filter(Wishlist.user_id == uid)
          .order_by(Wishlist.created_at.desc())
          .all()
    )
    return [
        {
            "perfume_id": row.perfume_id.hex(),  # BINARY(16) → hex 문자열
            "created_at": row.created_at,
        }
        for row in rows
    ]

@router.post("/wishlist")
def add_wishlist(
    perfume_id: str = Query(..., description="hex UUID of perfume"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    uid = _require_user_id(x_user_id)
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

    row = Wishlist(user_id=uid, perfume_id=pid)
    db.add(row)
    db.commit()
    return {"ok": True}

@router.delete("/wishlist")
def remove_wishlist(
    perfume_id: str = Query(..., description="hex UUID of perfume"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    uid = _require_user_id(x_user_id)
    try:
        pid = uuid_hex_to_bytes(perfume_id)
    except Exception:
        raise HTTPException(400, "invalid perfume_id (hex uuid)")

    row = (
        db.query(Wishlist)
          .filter(Wishlist.user_id == uid, Wishlist.perfume_id == pid)
          .first()
    )
    if not row:
        return {"ok": True, "deleted": 0}

    db.delete(row)
    db.commit()
    return {"ok": True, "deleted": 1}
