# backend/app/api/routes/catalog/brands.py
from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.db import get_db
from app.models.brand import Brand
from app.models.perfume import Perfume
from app.models.base import uuid_bytes_to_hex, uuid_hex_to_bytes

router = APIRouter(prefix="/catalog", tags=["Catalog"])

def _serialize_brand(b: Brand, perfume_count: int | None = None):
    return {
        "id": uuid_bytes_to_hex(b.id),
        "name": b.name,
        "logo_url": getattr(b, "logo_url", None),
        "perfume_count": perfume_count,
    }

@router.get("/brands")
def list_brands(
    q: str | None = Query(None, min_length=2, description="브랜드명 검색"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    # 브랜드별 향수 수를 함께 반환
    sub = (
        db.query(Perfume.brand_id, func.count(Perfume.id).label("c"))
        .group_by(Perfume.brand_id)
        .subquery()
    )
    qry = (
        db.query(Brand, func.coalesce(sub.c.c, 0))
        .outerjoin(sub, Brand.id == sub.c.brand_id)
        .order_by(func.coalesce(sub.c.c, 0).desc(), Brand.name.asc())
    )
    if q:
        like = f"%{q}%"
        qry = qry.filter(Brand.name.ilike(like))

    rows = qry.offset(offset).limit(limit).all()
    return [_serialize_brand(b, c) for b, c in rows]

@router.get("/brands/popular")
def popular_brands(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    sub = (
        db.query(Perfume.brand_id, func.count(Perfume.id).label("c"))
        .group_by(Perfume.brand_id)
        .subquery()
    )
    rows = (
        db.query(Brand, func.coalesce(sub.c.c, 0))
        .outerjoin(sub, Brand.id == sub.c.brand_id)
        .order_by(func.coalesce(sub.c.c, 0).desc(), Brand.name.asc())
        .limit(limit)
        .all()
    )
    return [_serialize_brand(b, c) for b, c in rows]

@router.get("/brands/{brand_id}/perfumes")
def perfumes_by_brand(
    brand_id: str = Path(..., description="hex UUID"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: str | None = Query(None, description="popular|recent"),
    gender: str | None = Query(None, description="men|women|unisex"),
    db: Session = Depends(get_db),
):
    bid = uuid_hex_to_bytes(brand_id)
    brand = db.get(Brand, bid)
    if not brand:
        raise HTTPException(404, "brand not found")

    q = db.query(Perfume).filter(Perfume.brand_id == bid)
    if gender:
        q = q.filter(Perfume.gender == gender)

    if sort == "popular":
        q = q.order_by(Perfume.view_count.desc(), Perfume.wish_count.desc(), Perfume.id.desc())
    else:
        q = q.order_by(Perfume.created_at.desc(), Perfume.id.desc())

    items = q.offset(offset).limit(limit).all()
    return {
        "brand": _serialize_brand(brand),
        "items": [
            {
                "id": uuid_bytes_to_hex(p.id),
                "name": p.name,
                "image_url": p.image_url,
                "gender": p.gender,
                "view_count": p.view_count,
                "wish_count": p.wish_count,
            }
            for p in items
        ],
    }
