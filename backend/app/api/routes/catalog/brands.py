# backend/app/api/routes/catalog/brands.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.db import get_db
from app.models.brand import Brand
from app.models.perfume import Perfume
from app.models.base import uuid_bytes_to_hex, uuid_hex_to_bytes

router = APIRouter(prefix="/catalog", tags=["Catalog"])


# ────────────────────────────────
# 내부 헬퍼: Brand 직렬화
# ────────────────────────────────
def _serialize_brand(b: Brand, perfume_count: int | None = None):
    return {
        "id": uuid_bytes_to_hex(b.id),
        "name": b.name,
        "logo_url": b.logo_url,
        "perfume_count": perfume_count,
    }


# ────────────────────────────────
# [1] 브랜드 리스트
# ────────────────────────────────
@router.get("/brands")
def list_brands(
    q: str | None = Query(None, min_length=1, description="브랜드명 부분검색"),
    sort: str | None = Query("popular", description="정렬 기준 (name|popular|recent)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    # Perfume 개수 서브쿼리
    pc = (
        db.query(Perfume.brand_id.label("bid"), func.count(Perfume.id).label("cnt"))
        .group_by(Perfume.brand_id)
        .subquery()
    )

    qy = (
        db.query(Brand, func.coalesce(pc.c.cnt, 0).label("perfume_count"))
        .outerjoin(pc, pc.c.bid == Brand.id)
    )

    if q:
        like = f"%{q}%"
        qy = qy.filter(Brand.name.ilike(like))

    # 정렬 옵션
    if sort == "name":
        qy = qy.order_by(Brand.name.asc())
    elif sort == "recent":
        qy = qy.order_by(Brand.id.desc())
    else:  # popular (기본)
        qy = qy.order_by(func.coalesce(pc.c.cnt, 0).desc(), Brand.name.asc())

    rows = qy.offset(offset).limit(limit).all()
    return [_serialize_brand(b, perfume_count=cnt) for b, cnt in rows]


# ────────────────────────────────
# [2] 특정 브랜드 정보 조회
# ────────────────────────────────
@router.get("/brands/{brand_id}")
def get_brand(
    brand_id: str = Path(..., description="hex 형식 UUID"),
    db: Session = Depends(get_db),
):
    try:
        bid = uuid_hex_to_bytes(brand_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid brand_id: hex UUID 사용")

    b = db.get(Brand, bid)
    if not b:
        raise HTTPException(status_code=404, detail="brand not found")

    cnt = db.query(func.count(Perfume.id)).filter(Perfume.brand_id == bid).scalar() or 0
    return _serialize_brand(b, perfume_count=cnt)


# ────────────────────────────────
# [3] 브랜드별 향수 리스트
# ────────────────────────────────
@router.get("/brands/{brand_id}/perfumes")
def list_brand_perfumes(
    brand_id: str = Path(..., description="hex 형식 UUID"),
    gender: str | None = Query(None, description="men|women|unisex"),
    sort: str | None = Query("recent", description="정렬 기준 (popular|recent)"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    try:
        bid = uuid_hex_to_bytes(brand_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid brand_id: hex UUID 사용")

    brand = db.get(Brand, bid)
    if not brand:
        raise HTTPException(status_code=404, detail="brand not found")

    qy = db.query(Perfume).filter(Perfume.brand_id == bid)
    if gender:
        qy = qy.filter(Perfume.gender == gender)

    if sort == "popular":
        qy = qy.order_by(
            Perfume.view_count.desc(),
            Perfume.wish_count.desc(),
            Perfume.id.desc(),
        )
    else:  # recent
        qy = qy.order_by(Perfume.created_at.desc(), Perfume.id.desc())

    items = qy.offset(offset).limit(limit).all()
    return [
        {
            "id": uuid_bytes_to_hex(p.id),
            "name": p.name,
            "brand_name": p.brand_name,
            "image_url": p.image_url,
            "gender": p.gender,
            "view_count": p.view_count,
            "wish_count": p.wish_count,
        }
        for p in items
    ]
