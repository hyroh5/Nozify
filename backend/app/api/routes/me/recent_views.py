from __future__ import annotations
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.db import get_db
from app.models.recent_view import RecentView
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

@router.get("/recent-views")
def get_recent_views(
    limit: int = Query(10, ge=1, le=50),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    uid = _require_user(x_user_id)
    rows = (
        db.query(RecentView)
          .filter(RecentView.user_id == uid)
          .order_by(desc(RecentView.viewed_at))
          .limit(limit)
          .all()
    )
    return [_ser_perfume(r.perfume) for r in rows]
