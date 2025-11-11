# backend/app/api/routes/catalog/search.py
from __future__ import annotations
from typing import List, Tuple

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.core.db import get_db
from app.models.perfume import Perfume
from app.models.brand import Brand
from app.models.base import uuid_bytes_to_hex

router = APIRouter(prefix="/catalog", tags=["Catalog"])

# -------------------------------------------------
# 기존: 향수 전용 검색 (그대로 유지)
# GET /catalog/search
# -------------------------------------------------
def _perfume_item(p: Perfume):
    return {
        "id": uuid_bytes_to_hex(p.id),
        "name": p.name,
        "brand_name": p.brand_name,
        "image_url": p.image_url,
        "gender": p.gender,
        "price": float(p.price) if p.price is not None else None,
        "currency": p.currency,
        "view_count": p.view_count,
        "wish_count": p.wish_count,
    }

@router.get("/search")
def search_perfumes(
    q: str | None = Query(None, min_length=2, description="이름/브랜드명 부분검색"),
    gender: str | None = Query(None, description="men / women / unisex"),
    sort: str | None = Query("recent", description="recent | popular"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Perfume)

    if q:
        like = f"%{q}%"
        # lower(...) like lower(...) 구현
        query = query.filter(
            or_(
                func.lower(Perfume.name).like(func.lower(like)),
                func.lower(Perfume.brand_name).like(func.lower(like)),
            )
        )
    if gender:
        query = query.filter(Perfume.gender == gender)

    if sort == "popular":
        query = query.order_by(Perfume.view_count.desc(), Perfume.wish_count.desc(), Perfume.id.desc())
    else:
        query = query.order_by(Perfume.created_at.desc(), Perfume.id.desc())

    rows = query.offset(offset).limit(limit).all()
    return [_perfume_item(p) for p in rows]


# -------------------------------------------------
# 추가 1: 통합 검색 (브랜드 + 향수 동시)
# GET /catalog/search_all
# -------------------------------------------------
def _brand_min(b: Brand, perfume_count: int | None = None):
    return {
        "id": uuid_bytes_to_hex(b.id),
        "name": b.name,
        "logo_url": getattr(b, "logo_url", None),
        "perfume_count": perfume_count,
    }

def _score_name(name: str, q: str) -> float:
    if not name:
        return 0.0
    n = name.lower()
    query = q.lower()
    if n.startswith(query):
        return 1.0
    if query in n:
        return 0.6
    return 0.0

def _score_perfume(p: Perfume, q: str) -> float:
    s1 = _score_name(p.name or "", q)
    s2 = _score_name(p.brand_name or "", q) * 0.8
    # 메인 어코드에 q가 들어가면 약간의 보너스
    bonus = 0.15 if any((isinstance(a, str) and q.lower() in a.lower()) for a in (p.main_accords or [])) else 0.0
    return s1 + s2 + bonus

def _score_brand(b: Brand, q: str) -> float:
    return _score_name(b.name or "", q)

@router.get("/search_all")
def search_all(
    q: str = Query(..., min_length=2, description="검색어(2자 이상)"),
    type: str = Query("all", regex="^(all|perfumes|brands)$"),
    gender: str | None = Query(None, description="men|women|unisex (향수 검색에만 적용)"),
    limit: int = Query(20, ge=1, le=50, description="총 반환 상한(엔티티별 분배)"),
    db: Session = Depends(get_db),
):
    perfumes_out: List[dict] = []
    brands_out: List[dict] = []

    # 향수 후보
    if type in ("all", "perfumes"):
        pq = (
            db.query(Perfume)
              .filter(
                  or_(
                      Perfume.name.ilike(f"%{q}%"),
                      Perfume.brand_name.ilike(f"%{q}%"),
                  )
              )
        )
        if gender:
            pq = pq.filter(Perfume.gender == gender)

        perfume_candidates: List[Perfume] = (
            pq.order_by(Perfume.view_count.desc(), Perfume.created_at.desc(), Perfume.id.desc())
              .limit(min(200, limit * 5))
              .all()
        )
        scored = [(_score_perfume(p, q), p) for p in perfume_candidates]
        scored.sort(key=lambda x: x[0], reverse=True)
        perfumes_out = [_perfume_item(p) | {"score": round(float(s), 3)} for s, p in scored[:limit]]

    # 브랜드 후보(+ 향수 수)
    if type in ("all", "brands"):
        pc = (
            db.query(Perfume.brand_id.label("bid"), func.count(Perfume.id).label("cnt"))
              .group_by(Perfume.brand_id)
              .subquery()
        )
        bq = (
            db.query(Brand, func.coalesce(pc.c.cnt, 0).label("perfume_count"))
              .outerjoin(pc, pc.c.bid == Brand.id)
              .filter(Brand.name.ilike(f"%{q}%"))
              .order_by(func.coalesce(pc.c.cnt, 0).desc(), Brand.name.asc())
              .limit(min(100, limit * 3))
              .all()
        )
        scored_b: List[Tuple[float, Brand, int]] = [(_score_brand(b, q), b, cnt) for (b, cnt) in bq]
        scored_b.sort(key=lambda x: x[0], reverse=True)
        # all 모드면 perfumes와 균형을 위해 brands는 절반 정도만
        take_n = max(1, limit // 2 if type == "all" else limit)
        brands_out = [_brand_min(b, perfume_count=cnt) | {"score": round(float(s), 3)} for (s, b, cnt) in scored_b[:take_n]]

    return {
        "q": q,
        "type": type,
        "perfumes": perfumes_out,
        "brands": brands_out,
    }


# -------------------------------------------------
# 추가 2: 자동완성 서제스트
# GET /catalog/suggest
# -------------------------------------------------
@router.get("/suggest")
def suggest(
    q: str = Query(..., min_length=2),
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db),
):
    # 향수명 후보: 이름별 그룹핑 후 인기/최신 순 정렬
    pq_rows = (
        db.query(
            Perfume.name.label("name"),
            func.max(Perfume.view_count).label("v"),
            func.max(Perfume.created_at).label("c"),
        )
        .filter(Perfume.name.ilike(f"%{q}%"))
        .group_by(Perfume.name)
        .order_by(func.max(Perfume.view_count).desc(), func.max(Perfume.created_at).desc())
        .limit(50)
        .all()
    )
    perfume_names = [r.name for r in pq_rows]

    # 브랜드명 후보: 단순 이름 매치
    bq_rows = (
        db.query(Brand.name.label("name"))
        .filter(Brand.name.ilike(f"%{q}%"))
        .order_by(Brand.name.asc())
        .limit(50)
        .all()
    )
    brand_names = [r.name for r in bq_rows]

    def _score_text(s: str) -> float:
        s_low = (s or "").lower()
        q_low = q.lower()
        if s_low.startswith(q_low):
            return 1.0
        if q_low in s_low:
            return 0.6
        return 0.0

    candidates = [("perfume", n, _score_text(n)) for n in perfume_names] + \
                 [("brand", n, _score_text(n)) for n in brand_names]

    candidates.sort(key=lambda x: x[2], reverse=True)
    items = [{"type": typ, "name": name, "score": round(float(sc), 3)}
             for typ, name, sc in candidates[:limit]]

    return {"q": q, "items": items}