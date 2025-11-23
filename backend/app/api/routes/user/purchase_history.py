# backend/app/api/routes/user/purchase_history.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from app.core.db import get_db
from app.models.purchase_history import PurchaseHistory
from app.models.perfume import Perfume
from app.models.user import User
from app.models.base import uuid_hex_to_bytes, uuid_bytes_to_hex
from app.api.deps import get_current_user_id

router = APIRouter(tags=["User"])


def _serialize_purchase(row: PurchaseHistory):
    p = row.perfume
    if not p:
        return None
    return {
        "added_at": row.created_at.isoformat(),
        "perfume": {
            "id": uuid_bytes_to_hex(p.id),
            "name": p.name,
            "brand_name": p.brand_name,
            "image_url": p.image_url,
            "gender": p.gender
        }
    }


@router.get("/purchase-history")
def get_purchase_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uid: User = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if uid is None:
        raise HTTPException(401, "Authentication required")

    rows = (
        db.query(PurchaseHistory)
        .options(joinedload(PurchaseHistory.perfume))
        .filter(PurchaseHistory.user_id == uid.id)
        .order_by(PurchaseHistory.created_at.desc())
        .offset(offset).limit(limit).all()
    )

    results = [r for r in [_serialize_purchase(x) for x in rows] if r is not None]
    return results


@router.post("/purchase-history")
def add_purchase_history(
    perfume_id: str,
    uid: User = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if uid is None:
        raise HTTPException(401, "Authentication required")

    try:
        pid = uuid_hex_to_bytes(perfume_id)
    except Exception:
        raise HTTPException(400, "invalid perfume_id (hex uuid)")

    p = db.get(Perfume, pid)
    if not p:
        raise HTTPException(404, "perfume not found")

    # 중복 방지
    exists = (
        db.query(PurchaseHistory)
        .filter(PurchaseHistory.user_id == uid.id, PurchaseHistory.perfume_id == pid)
        .first()
    )
    if exists:
        return {"ok": True, "duplicated": True}

    row = PurchaseHistory(
        user_id=uid.id,
        perfume_id=pid,
        purchase_date=None,  # 날짜는 사용 안함
    )
    db.add(row)
    db.commit()

    return {"ok": True}


@router.delete("/purchase-history/{perfume_id}")
def remove_purchase_history(
    perfume_id: str,
    uid: User = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    if uid is None:
        raise HTTPException(401, "Authentication required")

    try:
        pid = uuid_hex_to_bytes(perfume_id)
    except Exception:
        raise HTTPException(400, "invalid perfume_id (hex uuid)")

    row = (
        db.query(PurchaseHistory)
        .filter(PurchaseHistory.user_id == uid.id, PurchaseHistory.perfume_id == pid)
        .first()
    )

    if not row:
        return {"ok": True, "deleted": 0}

    db.delete(row)
    db.commit()

    return {"ok": True, "deleted": 1}
