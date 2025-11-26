# backend/app/api/routes/recommendations_pbti.py

from __future__ import annotations

from typing import List, Dict, Tuple
import random

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.db import get_db
from app.api.deps import get_current_user_id
from app.models.user import User
from app.models.perfume import Perfume
from app.models.brand import Brand
from app.models.pbti_result import PBTIResult
from app.models.base import uuid_bytes_to_hex

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)

# ---------------------------------------------------------
# 1) PBTI 타입별 설정
#   - 실제 PBTI 결과 코드(result_code)에 맞게 key 이름만 맞춰주면 됨
# ---------------------------------------------------------

PBTI_CONFIG: Dict[str, Dict] = {
    # 예시) 따뜻하고 묵직한 향 좋아하는 타입
    "WARM_HEAVY": {
        # 상단 문구에 쓸 수 있는 키워드 조합들
        "phrases": [
            ("Warm", "Heavy"),
            ("Sweet", "Heavy"),
            ("Warm", "Sweet"),
        ],
        # accord 가중치 (이 타입이 좋아하는 계열)
        "accord_weights": {
            "amber": 0.35,
            "woody": 0.3,
            "vanilla": 0.25,
            "spicy": 0.2,
            "sweet": 0.15,
        },
    },

    # 예시) 시원하고 깨끗한 타입
    "FRESH_CLEAN": {
        "phrases": [
            ("Fresh", "Clean"),
            ("Fresh", "Light"),
            ("Green", "Fresh"),
        ],
        "accord_weights": {
            "citrus": 0.35,
            "green": 0.3,
            "aquatic": 0.25,
            "ozonic": 0.2,
            "fresh spicy": 0.15,
        },
    },

    # 예시) 달콤하고 부드러운 타입
    "SWEET_SOFT": {
        "phrases": [
            ("Sweet", "Soft"),
            ("Gourmand", "Cozy"),
            ("Sweet", "Warm"),
        ],
        "accord_weights": {
            "sweet": 0.35,
            "gourmand": 0.3,
            "vanilla": 0.25,
            "powdery": 0.2,
            "fruity": 0.15,
        },
    },
    # ... 실제 PBTI 타입에 맞춰서 추가로 정의하면 됨
}

# ---------------------------------------------------------
# 2) 유틸: 최신 PBTI 결과 가져오기
# ---------------------------------------------------------


def get_latest_pbti_result(db: Session, user_id: bytes) -> PbtiResult | None:
    """
    해당 유저의 가장 최신 PBTI 결과 한 개를 가져온다.
    PbtiResult 모델 필드명은 실제 정의에 맞게 수정 필요.
    """
    return (
        db.query(PbtiResult)
        .filter(PbtiResult.user_id == user_id)
        .order_by(PbtiResult.created_at.desc())
        .first()
    )


# ---------------------------------------------------------
# 3) 향수 스코어 계산
# ---------------------------------------------------------


def _pbti_accord_score(
    accord_weights: Dict[str, float],
    main_accords: list | None,
) -> float:
    """
    main_accords 배열에 들어있는 accord 들이
    PBTI 타입에서 얼마나 선호되는지 합산.
    """
    if not accord_weights or not main_accords:
        return 0.0

    score = 0.0
    for acc in main_accords:
        if not isinstance(acc, str):
            continue
        # 완전 일치 우선, 없으면 소문자 비교 정도는 해볼 수 있음
        w = accord_weights.get(acc)
        if w is None:
            # 이름이 미묘하게 다를 수 있으니 소문자 키로도 한 번 시도
            w = accord_weights.get(acc.lower(), 0.0)
        score += w or 0.0

    return float(round(score, 3))


def _popularity_score(p: Perfume) -> float:
    """
    기본 인기 점수 (view / wish / purchase 가중합)
    """
    v = float(p.view_count or 0)
    w = float(p.wish_count or 0)
    pc = float(p.purchase_count or 0)

    return float(
        0.01 * min(v, 5000) +
        0.03 * min(w, 2000) +
        0.1 * min(pc, 500)
    )


# ---------------------------------------------------------
# 4) 라우터: PBTI 기반 추천
# ---------------------------------------------------------


@router.get("/pbti")
def recommend_by_pbti(
    limit: int = Query(10, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
):
    """
    4. Warm, Heavy한 당신에게 어울리는 향이에요 (PBTI 기반 추천)

    - 사용자의 최신 PBTI 결과를 조회
    - 해당 타입에 정의된 accord preference 기반으로 향수 점수 계산
    - 인기(popularity)를 살짝 섞어서 최종 상위 N개 반환
    - 상단 문구는 PBTI 타입에 정의된 phrase 후보들 중 랜덤 1개를 사용
    """

    # 1) 최신 PBTI 결과
    pbti = get_latest_pbti_result(db, current_user.id)
    if not pbti:
        raise HTTPException(status_code=404, detail="PBTI 결과가 없습니다. 먼저 PBTI 테스트를 완료해주세요.")

    # PbtiResult 모델에서 실제 필드 이름에 맞게 수정 필요
    pbti_code: str = pbti.result_code  # 예: "WARM_HEAVY" / "FRESH_CLEAN" 등

    config = PBTI_CONFIG.get(pbti_code)
    if not config:
        # PBTI 결과는 있는데 아직 매핑을 안 한 타입
        raise HTTPException(status_code=400, detail=f"PBTI 타입 매핑이 정의되지 않았습니다: {pbti_code}")

    accord_weights: Dict[str, float] = config["accord_weights"]
    phrase_candidates: List[Tuple[str, str]] = config["phrases"]

    # 2) 상단 문구 랜덤 선택
    kw1, kw2 = random.choice(phrase_candidates)
    heading = f"{kw1}, {kw2}한 당신에게 어울리는 향이에요"

    # 3) 향수 후보군 쿼리
    #    너무 많이 돌리기 부담되면 상위 1000개 정도만 먼저 가져옴
    perfumes: List[Perfume] = (
        db.query(Perfume)
        .join(Brand, Perfume.brand_id == Brand.id)
        .limit(1000)
        .all()
    )

    scored: List[tuple[float, Perfume, Brand]] = []

    # Brand 정보 같이 가져오기 위해 간단히 map 구성
    # (위에서 join 했으니까 Perfume.brand 관계가 잡혀있다면 그냥 p.brand 써도 됨)
    brand_ids = {p.brand_id for p in perfumes}
    brands = db.query(Brand).filter(Brand.id.in_(brand_ids)).all()
    brand_map = {b.id: b for b in brands}

    for p in perfumes:
        brand = brand_map.get(p.brand_id)
        if not brand:
            continue

        accord_score = _pbti_accord_score(accord_weights, p.main_accords or [])
        pop_score = _popularity_score(p)

        # 취향 0.7 + 인기 0.3 정도로 섞기
        final_score = 0.7 * accord_score + 0.3 * pop_score

        if final_score <= 0:
            continue

        scored.append((final_score, p, brand))

    if not scored:
        return {
            "pbti_type": pbti_code,
            "heading": heading,
            "items": [],
        }

    scored.sort(key=lambda x: x[0], reverse=True)

    items = []
    for score, p, b in scored[:limit]:
        items.append(
            {
                "id": uuid_bytes_to_hex(p.id),
                "name": p.name,
                "brand_name": b.name,
                "image_url": p.image_url,
                "gender": p.gender,
                "view_count": p.view_count,
                "wish_count": p.wish_count,
                "score": float(round(score, 3)),
            }
        )

    return {
        "pbti_type": pbti_code,
        "heading": heading,
        "items": items,
    }
