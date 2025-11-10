# backend/app/api/routes/catalog/perfumes.py
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
        "view_count": p.view_count,
        "wish_count": p.wish_count,
        "purchase_count": p.purchase_count,
    }

@router.get("/perfumes/{perfume_id}")
def get_perfume(
    perfume_id: str = Path(..., description="hex 형식 UUID"),
    track_view: bool = Query(True, description="상세 조회 시 view_count 증가"),
    db: Session = Depends(get_db),
):
    p = db.get(Perfume, uuid_hex_to_bytes(perfume_id))
    if not p:
        raise HTTPException(404, "perfume not found")

    # 조회수 증가
    if track_view:
        p.view_count = int(p.view_count or 0) + 1
        db.commit()
        db.refresh(p)

    return _serialize_perfume(p)

@router.get("/perfumes")
def list_perfumes(
    brand_id: str | None = Query(None, description="hex 형식 UUID"),
    gender: str | None = Query(None, description="men / women / unisex"),
    q: str | None = Query(None, min_length=2, description="이름/브랜드 검색"),
    sort: str | None = Query(None, description="popular|recent"),
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

    # 정렬
    if sort == "popular":
        query = query.order_by(Perfume.view_count.desc(), Perfume.wish_count.desc(), Perfume.id.desc())
    else:  # default: recent
        query = query.order_by(Perfume.created_at.desc(), Perfume.id.desc())

    items = query.offset(offset).limit(limit).all()
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

# ─────────────────────────────────────────
# 유사 향수 추천 (간단한 교집합 기반)
# ─────────────────────────────────────────
def _jaccard(a: list | None, b: list | None) -> float:
    A = set(a or [])
    B = set(b or [])
    if not A and not B:
        return 0.0
    return len(A & B) / max(1, len(A | B))

def _extract_note_names(notes: list | None) -> list[str]:
    if not notes:
        return []
    # notes는 [{"name": "...", "imageUrl": "..."}, ...] 형태이므로 'name' 키 값만 추출
    return [n.get("name") for n in notes if isinstance(n, dict) and n.get("name")]

@router.get("/perfumes/{perfume_id}/similar")
def similar_perfumes(
    perfume_id: str = Path(..., description="기준 향수 hex UUID"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    base = db.get(Perfume, uuid_hex_to_bytes(perfume_id))
    if not base:
        raise HTTPException(404, "base perfume not found")

    # 후보군: 같은 성별 우선, 최근/인기순 섞어서 상위 300개 정도에서 계산
    candidates = (
        db.query(Perfume)
          .filter(Perfume.id != base.id)
          .filter(Perfume.gender == base.gender if base.gender else True)
          .order_by(Perfume.view_count.desc(), Perfume.created_at.desc())
          .limit(300)
          .all()
    )

    base_acc = base.main_accords or []
    base_top = _extract_note_names(base.top_notes)
    base_mid = _extract_note_names(base.middle_notes)
    base_base = _extract_note_names(base.base_notes)
    base_any = (base.general_notes or []) + base_top + base_mid + base_base

    scored = []
    for p in candidates:
        p_top = _extract_note_names(p.top_notes)
        p_any_notes = _extract_note_names(p.top_notes) + _extract_note_names(p.middle_notes) + _extract_note_names(p.base_notes)

        s_acc = _jaccard(base_acc, p.main_accords)
        s_top = _jaccard(base_top, p_top)
        s_any = _jaccard(base_any, (p.general_notes or []) + p_any_notes)
        score = 0.6 * s_acc + 0.2 * s_top + 0.2 * s_any
        if score <= 0:
            continue
        scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for score, p in scored[:limit]:
        item = _serialize_perfume(p)
        item["similarity"] = round(float(score), 4)
        out.append(item)
    return {
        "base_id": uuid_bytes_to_hex(base.id),
        "base_name": base.name,
        "results": out,
    }

@router.get("/perfumes/popular")
def popular_perfumes(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    items = (
        db.query(Perfume)
          .order_by(Perfume.view_count.desc(), Perfume.wish_count.desc(), Perfume.id.desc())
          .offset(offset)
          .limit(limit)
          .all()
    )
    return [_serialize_perfume(p) for p in items]
