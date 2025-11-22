# backend/app/api/routes/user/wishlist.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.wishlist import Wishlist
from app.models.perfume import Perfume
from app.models.base import uuid_hex_to_bytes, uuid_bytes_to_hex
from app.api.deps import get_current_user_id

router = APIRouter(tags=["User"])

@router.get("/wishlist")
def get_wishlist(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uid: bytes = Depends(get_current_user_id), 
    db: Session = Depends(get_db),
):
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
    uid: bytes = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
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

@router.delete("/wishlist/{perfume_id}")
def remove_wishlist(
    perfume_id: str,
    uid: bytes = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
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
