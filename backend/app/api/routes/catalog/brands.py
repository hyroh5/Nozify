from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.db import get_db
from app.models.brand import Brand
from app.models.perfume import Perfume
from app.models.base import uuid_bytes_to_hex

router = APIRouter(prefix="/catalog", tags=["Catalog"])

@router.get("/brands")
def list_brands(
    q: str | None = Query(None, min_length=1, description="브랜드명 검색"),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    subq = (
        db.query(Perfume.brand_id, func.count(Perfume.id).label("perfume_count"))
          .group_by(Perfume.brand_id)
          .subquery()
    )
    query = (
        db.query(Brand, func.coalesce(subq.c.perfume_count, 0))
          .outerjoin(subq, subq.c.brand_id == Brand.id)
          .order_by(Brand.name.asc())
    )
    if q:
        query = query.filter(Brand.name.ilike(f"%{q}%"))
    rows = query.limit(limit).all()
    return [
        {
            "id": uuid_bytes_to_hex(b.id),
            "name": b.name,
            "logo_url": b.logo_url,
            "perfume_count": int(cnt or 0),
        }
        for b, cnt in rows
    ]
