# backend/app/api/routes/recommendations_brand.py

from __future__ import annotations

from typing import List, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.db import get_db
from app.api.deps import get_current_user_id
from app.models.user import User
from app.models.brand import Brand
from app.models.perfume import Perfume
from app.models.recent_view import RecentView
from app.models.wishlist import Wishlist
from app.models.purchase_history import PurchaseHistory
from app.models.base import uuid_bytes_to_hex, uuid_hex_to_bytes
from app.services.user_preference_service import get_or_build_user_preference

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)

# ---------------------------------------------------------
# 유저 활동 로그 기반으로 "자주 보는 브랜드" 점수 계산
# ---------------------------------------------------------


def _calc_brand_scores_for_user(db: Session, user: User) -> Dict[bytes, float]:
    """
    RecentView / Wishlist / PurchaseHistory 를 이용해서
    브랜드별 점수를 계산한다.
    key: brand_id (bytes, Brand.id)
    """
    scores: Dict[bytes, float] = {}

    # 1) 최근 본 향수 → 가중치 1
    rv_rows = (
        db.query(Perfume.brand_id, func.count(RecentView.id))
        .join(RecentView, RecentView.perfume_id == Perfume.id)
        .filter(RecentView.user_id == user.id)
        .group_by(Perfume.brand_id)
        .all()
    )
    for brand_id, cnt in rv_rows:
        scores[brand_id] = scores.get(brand_id, 0.0) + float(cnt) * 1.0

    # 2) 위시리스트 → 가중치 3
    wl_rows = (
        db.query(Perfume.brand_id, func.count(Wishlist.id))
        .join(Wishlist, Wishlist.perfume_id == Perfume.id)
        .filter(Wishlist.user_id == user.id)
        .group_by(Perfume.brand_id)
        .all()
    )
    for brand_id, cnt in wl_rows:
        scores[brand_id] = scores.get(brand_id, 0.0) + float(cnt) * 3.0

    # 3) 구매 이력 → 가중치 5
    ph_rows = (
        db.query(Perfume.brand_id, func.count(PurchaseHistory.id))
        .join(PurchaseHistory, PurchaseHistory.perfume_id == Perfume.id)
        .filter(PurchaseHistory.user_id == user.id)
        .group_by(Perfume.brand_id)
        .all()
    )
    for brand_id, cnt in ph_rows:
        scores[brand_id] = scores.get(brand_id, 0.0) + float(cnt) * 5.0

    return scores


def _fallback_trending_brands(db: Session, limit: int) -> List[dict]:
    """
    유저 로그가 거의 없을 때용 기본 브랜드 추천.
    Perfume 의 view_count / wish_count / purchase_count 를
    브랜드 단위로 합산해서 상위 브랜드를 반환한다.
    """
    rows = (
        db.query(
            Perfume.brand_id,
            func.sum(func.coalesce(Perfume.view_count, 0)).label("v"),
            func.sum(func.coalesce(Perfume.wish_count, 0)).label("w"),
            func.sum(func.coalesce(Perfume.purchase_count, 0)).label("p"),
        )
        .group_by(Perfume.brand_id)
        .all()
    )

    scored: List[tuple[float, bytes]] = []
    for brand_id, v, w, p in rows:
        score = float(v or 0) * 0.01 + float(w or 0) * 0.03 + float(p or 0) * 0.1
        scored.append((score, brand_id))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_ids = [b_id for _, b_id in scored[:limit]]

    if not top_ids:
        return []

    brands = (
        db.query(Brand)
        .filter(Brand.id.in_(top_ids))
        .all()
    )

    # id 순서 유지 위해 dict
    brand_map = {b.id: b for b in brands}
    result: List[dict] = []
    for b_id in top_ids:
        b = brand_map.get(b_id)
        if not b:
            continue
        result.append(
            {
                "brand_id": uuid_bytes_to_hex(b.id),
                "brand_name": b.name,
                "logo_url": b.logo_url,
                "score": None,
            }
        )
    return result


# ---------------------------------------------------------
# 3-1. 내가 자주 보는 브랜드 리스트
# ---------------------------------------------------------


@router.get("/brands")
def my_favorite_brands(
    limit: int = Query(7, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
):
    """
    3. 내가 자주 보는 브랜드 추천
    - 최근 본 향수 / 위시 / 구매 이력을 합쳐서
      브랜드별 점수를 계산하고 상위 N개를 반환.
    - brand 테이블은 (id, name, logo_url) 만 사용.
    """

    # 1) 유저 활동 기반 점수 계산
    scores = _calc_brand_scores_for_user(db, current_user)

    # 활동이 거의 없으면 트렌딩 브랜드로 대체
    if not scores:
        return {"items": _fallback_trending_brands(db, limit)}

    # 점수 높은 순으로 정렬
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_brand_ids = [b_id for b_id, _ in sorted_items[: limit * 2]]  # 넉넉히 뽑기

    brands = (
        db.query(Brand)
        .filter(Brand.id.in_(top_brand_ids))
        .all()
    )
    brand_map = {b.id: b for b in brands}

    results: List[dict] = []
    for b_id, score in sorted_items:
        if b_id not in brand_map:
            continue
        b = brand_map[b_id]
        results.append(
            {
                "brand_id": uuid_bytes_to_hex(b.id),
                "brand_name": b.name,
                "logo_url": b.logo_url,
                "score": float(round(score, 3)),
            }
        )
        if len(results) >= limit:
            break

    # 혹시 모자라면 트렌딩 브랜드로 채워 넣어도 됨 (옵션)

    return {"items": results}


# ---------------------------------------------------------
# 3-2. 특정 브랜드의 향수를 "내 취향 순"으로 정렬
# ---------------------------------------------------------


def _extract_pref_accords(pref) -> Dict[str, float]:
    """
    user_preference.preferred_accords 를 안전하게 dict 형태로 변환.
    - 이미 dict 면 그대로 사용
    - list[{"name": "...", "score": ...}] 형태면 변환
    """
    if not pref or not getattr(pref, "preferred_accords", None):
        return {}

    raw = pref.preferred_accords
    if isinstance(raw, dict):
        return {str(k): float(v) for k, v in raw.items()}

    if isinstance(raw, list):
        out: Dict[str, float] = {}
        for item in raw:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("accord")
            score = item.get("score", 1.0)
            if name:
                out[str(name)] = float(score)
        return out

    return {}


def _match_score_by_accords(pref_accords: Dict[str, float], main_accords: list | None) -> float:
    """
    간단한 v1 스코어:
    - 향수 main_accords 배열에 포함된 accord 가
      사용자 선호도에 있으면 그 값을 더한다.
    """
    if not pref_accords or not main_accords:
        return 0.0

    s = 0.0
    for acc in main_accords:
        if not isinstance(acc, str):
            continue
        s += pref_accords.get(acc, 0.0)
    return float(round(s, 3))


@router.get("/brands/{brand_id}/perfumes")
def perfumes_of_brand_for_user(
    brand_id: str = Path(..., description="hex UUID 형식 브랜드 id"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
):
    """
    3. 특정 브랜드 선택 시
    - 해당 브랜드의 향수를 사용자 취향 순으로 정렬해서 반환
    - 취향 정보가 부족하면 인기순으로 정렬
    """

    try:
        brand_pk = uuid_hex_to_bytes(brand_id)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid brand_id format")

    brand = db.query(Brand).get(brand_pk)
    if not brand:
        raise HTTPException(status_code=404, detail="brand not found")

    # 이 브랜드의 향수 전체 가져오기 (적당히 상한선)
    perfumes = (
        db.query(Perfume)
        .filter(Perfume.brand_id == brand_pk)
        .all()
    )

    if not perfumes:
        return {
            "brand": {
                "brand_id": brand_id,
                "brand_name": brand.name,
                "logo_url": brand.logo_url,
            },
            "items": [],
        }

    # 사용자 취향 프로필 읽어오기
    user_pref = get_or_build_user_preference(db, current_user.id)
    pref_accords = _extract_pref_accords(user_pref)

    scored = []
    for p in perfumes:
        # 1) 취향 기반 점수
        accord_score = _match_score_by_accords(pref_accords, p.main_accords or [])

        # 2) 기본 인기 보정
        pop_score = (
            float(p.view_count or 0) * 0.01
            + float(p.wish_count or 0) * 0.03
            + float(p.purchase_count or 0) * 0.1
        )

        if pref_accords:
            final_score = 0.7 * accord_score + 0.3 * pop_score
        else:
            final_score = pop_score

        scored.append((final_score, p))

    scored.sort(key=lambda x: x[0], reverse=True)

    items: List[dict] = []
    for score, p in scored[:limit]:
        items.append(
            {
                "id": uuid_bytes_to_hex(p.id),
                "name": p.name,
                "brand_name": brand.name,
                "image_url": p.image_url,
                "gender": p.gender,
                "view_count": p.view_count,
                "wish_count": p.wish_count,
                "score": float(round(score, 3)),
            }
        )

    return {
        "brand": {
            "brand_id": uuid_bytes_to_hex(brand.id),
            "brand_name": brand.name,
            "logo_url": brand.logo_url,
        },
        "items": items,
    }
