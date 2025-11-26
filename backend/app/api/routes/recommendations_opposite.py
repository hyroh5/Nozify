# backend/app/api/routes/recommendations_opposite.py

from __future__ import annotations

from typing import Dict, Any, List

import random
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.api.deps import get_current_user_id
from app.models.user import User
from app.models.perfume import Perfume
from app.models.base import uuid_bytes_to_hex
from app.services.user_preference_service import get_or_build_user_preference

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


# -----------------------------------------
# 헬퍼: user_preference.preferred_accords 정규화
# -----------------------------------------
def _normalize_pref_accords(raw: Any) -> Dict[str, float]:
    """
    user_preference.preferred_accords 가
    - {"citrus": 1.2, "woody": 0.8} 형태이든
    - ["citrus", "woody"] 형태이든
    둘 다 받아서 dict 로 통일.
    """
    if isinstance(raw, dict):
        return {str(k): float(v) for k, v in raw.items()}

    if isinstance(raw, list):
        return {str(name): 1.0 for name in raw}

    return {}


# -----------------------------------------
# 헬퍼: accord 기반 유사도 (0 ~ 1)
# -----------------------------------------
def _accord_similarity(
    pref_accords: Dict[str, float],
    perfume_accords: List[str] | None,
) -> float:
    """
    아주 단순한 accord 기반 취향 유사도.
    - pref_accords: {"citrus": 1.2, "woody": 0.8, ...}
    - perfume_accords: ["citrus", "green", ...]
    """
    if not pref_accords or not perfume_accords:
        return 0.0

    accords_set = set(perfume_accords)
    inter_weight = sum(
        w for name, w in pref_accords.items() if name in accords_set
    )
    total_weight = sum(pref_accords.values()) or 1.0
    return float(inter_weight / total_weight)


# -----------------------------------------
# 헬퍼: 간단 인기 점수 (0 ~ 1 근처)
# -----------------------------------------
def _popularity_score(p: Perfume) -> float:
    v = float(p.view_count or 0)
    w = float(p.wish_count or 0)
    pc = float(p.purchase_count or 0)

    # 대략적인 스케일링 (상한선을 둬서 너무 큰 값은 잘라냄)
    raw = (
        0.01 * min(v, 5000)
        + 0.03 * min(w, 2000)
        + 0.1 * min(pc, 500)
    )
    # 0~1 정도로 눌러주기
    return float(max(0.0, min(1.0, raw / 5.0)))


# -----------------------------------------
# 6. 새로운 향 시도 – 반대 취향 추천
# -----------------------------------------
@router.get("/opposite")
def recommend_opposite_style(
    limit: int = Query(10, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
):
    """
    6. 새로운 향 시도
    - 사용자 선호 accords 와 최대한 "반대"에 있는 향수 추천
    - 취향 유사도(similarity)가 낮을수록, 인기(popularity)가 높을수록 점수 ↑
    """

    # 1) 로그인 필수
    user_id_bytes: bytes = current_user.id

    # 2) user_preference 가져오기 (없으면 계산해서 upsert)
    pref = get_or_build_user_preference(db, user_id_bytes)
    if not pref or not getattr(pref, "preferred_accords", None):
        # 취향 데이터가 없으면 추천이 애매하니 그냥 빈 리스트 반환
        return {
            "message": "사용자 취향 데이터가 없어 반대 취향 추천을 생성할 수 없습니다.",
            "items": [],
        }

    pref_accords = _normalize_pref_accords(pref.preferred_accords)
    if not pref_accords:
        return {
            "message": "사용자 취향 accords 정보가 비어 있습니다.",
            "items": [],
        }

    # 3) 후보 향수 로딩 (너무 많으면 부담이니 적당히 자름)
    candidates: List[Perfume] = (
        db.query(Perfume)
        .order_by(Perfume.view_count.desc(), Perfume.id.desc())
        .limit(600)
        .all()
    )

    scored: List[dict] = []

    for p in candidates:
        accords = p.main_accords or []
        sim = _accord_similarity(pref_accords, accords)  # 0 ~ 1
        distance = 1.0 - sim  # 0 ~ 1, 클수록 "반대"

        # 사용자의 취향과 너무 비슷한 애들은 제외
        if distance < 0.4:
            continue

        pop = _popularity_score(p)

        # 랜덤성 조금 섞기
        jitter = random.uniform(-0.05, 0.05)

        final_score = 0.7 * distance + 0.3 * pop + jitter
        final_score = float(max(0.0, min(1.0, final_score)))

        scored.append(
            {
                "id": uuid_bytes_to_hex(p.id),
                "name": p.name,
                "brand_name": p.brand_name,
                "image_url": p.image_url,
                "gender": p.gender,
                "similarity": round(float(sim), 3),
                "distance": round(float(distance), 3),
                "popularity": round(float(pop), 3),
                "score": round(final_score, 3),
            }
        )

    # 4) 점수 기준으로 정렬 후 상위 limit 개
    scored.sort(key=lambda x: x["score"], reverse=True)
    items = scored[:limit]

    return {
        "items": items,
    }
