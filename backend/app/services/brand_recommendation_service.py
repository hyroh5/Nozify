# app/services/brand_recommendation_service.py

from typing import Any, Dict, List

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.brand import Brand
from app.models.perfume import Perfume
from app.models.recent_view import RecentView
from app.models.base import uuid_bytes_to_hex, uuid_hex_to_bytes
from app.services.user_preference_service import get_or_build_user_preference


def get_user_top_brands(
    db: Session,
    user_id_bytes: bytes,
    limit: int = 7,
) -> List[Dict[str, Any]]:
    """
    사용자가 '자주 보는 브랜드' 상위 N개를 반환.
    기준: RecentView 기반으로 브랜드별 조회수 집계.
    """

    rows = (
        db.query(
            Perfume.brand_id.label("brand_id"),
            Brand.name.label("brand_name"),
            Brand.logo_url.label("brand_image_url"),
            func.count(RecentView.id).label("view_count"),
        )
        .join(Perfume, RecentView.perfume_id == Perfume.id)
        .join(Brand, Perfume.brand_id == Brand.id)
        .filter(RecentView.user_id == user_id_bytes)
        .group_by(Perfume.brand_id, Brand.name, Brand.logo_url)
        .order_by(desc("view_count"))
        .limit(limit)
        .all()
    )

    result: List[Dict[str, Any]] = []
    for r in rows:
        result.append(
            {
                "brand_id": uuid_bytes_to_hex(r.brand_id),
                "brand_name": r.brand_name,
                "brand_image_url": r.brand_image_url,
                "view_count": int(r.view_count),
            }
        )
    return result


def _compute_accord_similarity(
    user_pref: Dict[str, float],
    main_accords_percentage: Any,
) -> float:
    """
    user_preference의 accord 벡터와
    perfume.main_accords_percentage(JSON) 간의 유사도 계산.
    JSON 예시:
    [
      {"name": "floral", "percent": 35},
      {"name": "woody", "percent": 20},
      ...
    ]
    """
    if not user_pref or not main_accords_percentage:
        return 0.0

    total_weight = 0.0
    score = 0.0

    for item in main_accords_percentage:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not name:
            continue
        percent = float(item.get("percent", 0.0))
        total_weight += percent
        score += percent * float(user_pref.get(name, 0.0))

    if total_weight <= 0:
        return 0.0

    return float(score / total_weight)


def get_brand_perfumes_for_user(
    db: Session,
    user_id_bytes: bytes,
    brand_id_hex: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    특정 브랜드 내에서 '사용자 취향 유사도' 순으로 정렬된 향수 목록 반환.
    """

    brand_id_bytes = uuid_hex_to_bytes(brand_id_hex)

    # 1) 사용자 취향 벡터
    user_pref = get_or_build_user_preference(db, user_id_bytes)

    # 2) 해당 브랜드 향수들
    perfumes = (
        db.query(Perfume)
        .filter(Perfume.brand_id == brand_id_bytes)
        .all()
    )

    scored: List[Dict[str, Any]] = []
    for p in perfumes:
        sim = _compute_accord_similarity(
            user_pref=user_pref,
            main_accords_percentage=p.main_accords_percentage,
        )

        scored.append(
            {
                "id": uuid_bytes_to_hex(p.id),
                "name": p.name,
                "brand_id": uuid_bytes_to_hex(p.brand_id),
                "brand_name": p.brand_name,
                "image_url": p.image_url,
                "gender": p.gender,
                "similarity": round(sim, 4),
            }
        )

    # 유사도 내림차순 정렬
    scored.sort(key=lambda x: x["similarity"], reverse=True)

    return scored[:limit]
