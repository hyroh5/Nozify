from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.db import get_db
from app.models.perfume import Perfume
from app.models.base import uuid_bytes_to_hex, uuid_hex_to_bytes

router = APIRouter(prefix="/catalog", tags=["Catalog"])

def _serialize_perfume(p: Perfume):
    return {
        "id": uuid_bytes_to_hex(p.id),
        "name": p.name,
        "brand_id": uuid_bytes_to_hex(p.brand_id),
        "brand_name": p.brand_name,
        "image_url": p.image_url,
        "gender": p.gender,
        "price": float(p.price) if p.price is not None else None,
        "currency": p.currency,
        "longevity": float(p.longevity) if p.longevity is not None else None,
        "sillage": float(p.sillage) if p.sillage is not None else None,
        "main_accords": p.main_accords,
        "main_accords_percentage": p.main_accords_percentage,
        "top_notes": p.top_notes,
        "middle_notes": p.middle_notes,
        "base_notes": p.base_notes,
        "general_notes": p.general_notes,
        "season_ranking": p.season_ranking,
        "occasion_ranking": p.occasion_ranking,
        "purchase_url": p.purchase_url,
        "fragella_id": p.fragella_id,
    }

@router.get("/perfumes/{perfume_id}")
def get_perfume(
    perfume_id: str = Path(..., description="hex 형식 UUID"),
    db: Session = Depends(get_db),
):
    p = db.get(Perfume, uuid_hex_to_bytes(perfume_id))
    if not p:
        raise HTTPException(404, "perfume not found")
    return _serialize_perfume(p)

@router.get("/perfumes")
def list_perfumes(
    brand_id: str | None = Query(None, description="hex 형식 UUID"),
    gender: str | None = Query(None, description="men / women / unisex"),
    q: str | None = Query(None, min_length=2, description="이름/브랜드 검색"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Perfume)
    if brand_id:
        query = query.filter(Perfume.brand_id == uuid_hex_to_bytes(brand_id))
    if gender:
        query = query.filter(Perfume.gender == gender)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Perfume.name.ilike(like), Perfume.brand_name.ilike(like)))

    items = (
        query.order_by(Perfume.created_at.desc(), Perfume.id.desc())
             .offset(offset)
             .limit(limit)
             .all()
    )
    return [
        {
            "id": uuid_bytes_to_hex(p.id),
            "name": p.name,
            "brand_name": p.brand_name,
            "image_url": p.image_url,
            "gender": p.gender,
        }
        for p in items
    ]
