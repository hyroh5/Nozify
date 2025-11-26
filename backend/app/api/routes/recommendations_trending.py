# backend/app/api/routes/recommendations_trending.py

from __future__ import annotations

from typing import List, Dict, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.db import get_db
from app.models.perfume import Perfume
from app.models.base import uuid_bytes_to_hex

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


def _trending_score_expr():
    """
    view / wish / purchase를 가중합으로 만든 score 식.
    너무 큰 값은 최소화해서 과도하게 오래된 인기 향수에 끌려가지 않게 한다.
    """
    return (
        0.5 * func.least(Perfume.view_count, 5000) +
        0.3 * func.least(Perfume.wish_count, 2000) +
        0.2 * func.least(Perfume.purchase_count, 500)
    )


@router.get("/trending")
def get_trending_perfumes(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    5. 트렌딩
    - 전 사용자 기준 글로벌 트렌딩 향수 목록
    - view_count, wish_count, purchase_count 기반 가중합으로 score 계산
    - 개인화 없음, 비로그인도 호출 가능
    """
    score_expr = _trending_score_expr().label("trending_score")

    # Perfume + 계산된 trending_score 같이 조회
    rows = (
        db.query(Perfume, score_expr)
        .order_by(score_expr.desc(), Perfume.created_at.desc(), Perfume.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items: list[Dict[str, Any]] = []
    for p, s in rows:
        items.append(
            {
                "id": uuid_bytes_to_hex(p.id),
                "name": p.name,
                "brand_name": p.brand_name,
                "image_url": p.image_url,
                "gender": p.gender,
                "view_count": p.view_count,
                "wish_count": p.wish_count,
                "purchase_count": p.purchase_count,
                "trending_score": float(s or 0.0),
            }
        )

    return {"items": items}
