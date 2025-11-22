from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.db import get_db
from app.models.recent_view import RecentView
from app.models.perfume import Perfume
from app.models.base import uuid_bytes_to_hex
from app.api.deps import get_current_user_id

router = APIRouter(tags=["User"])

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
    db: Session = Depends(get_db),
    uid: bytes = Depends(get_current_user_id), 
):
    rows = (
        db.query(RecentView)
        .filter(RecentView.user_id == uid)
        .order_by(desc(RecentView.viewed_at))
        .limit(limit)
        .all()
    )
    return [_ser_perfume(r.perfume) for r in rows]
