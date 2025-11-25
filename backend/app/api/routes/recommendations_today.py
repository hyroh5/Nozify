from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import settings
from app.api.deps import get_current_user_id
from app.models.user import User
from app.models.perfume import Perfume
from app.models.base import uuid_bytes_to_hex


from datetime import datetime

from app.models.recent_view import RecentView
from app.schemas.recommendations import RecentViewedPerfume, RecentViewedList
from app.models.user import User

from app.services.weather_service import (
    fetch_weather,
    detect_season_from_date,
    adjust_weights_by_temp,
)
from app.services.user_preference_service import get_or_build_user_preference
from app.services.seasonal_recommendation_service import (
    season_score_map,
    calc_stability,
    ADJACENT_MAP,
)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


# ---------------------------------------------------------------------
# 헬퍼 함수들
# ---------------------------------------------------------------------
def _parse_occasion_scores(occasion_ranking: Any) -> Dict[str, float]:
    """
    Perfume.occasion_ranking JSON -> {occasion_name: score} 맵으로 변환
    """
    if not occasion_ranking:
        return {}

    out: Dict[str, float] = {}
    for item in occasion_ranking:
        name = item.get("name")
        score = item.get("score", 0.0)
        if not name:
            continue
        out[name] = float(score or 0.0)
    return out


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


def _calc_season_score(
    season: str,
    scores: Dict[str, float],
    weight_override: Dict[str, float],
) -> tuple[float, float, float, float]:
    """
    계절 점수 + 안정성 기반 score 계산
    (기존 seasonal_recommendation_service 의 로직을 여기서 간략히 재사용)
    """
    from app.services.seasonal_recommendation_service import SEASONS

    adj1, adj2 = ADJACENT_MAP[season]

    current = scores.get(season, 0.0)
    a1 = scores.get(adj1, 0.0)
    a2 = scores.get(adj2, 0.0)
    stability = calc_stability(scores)

    w = weight_override
    base = (
        current * w["current"]
        + a1 * w["adj1"]
        + a2 * w["adj2"]
        + stability * w["stability"]
    )

    return float(current), float(a1), float(stability), float(base)


def _calc_weather_boost(
    temp: float,
    humidity: int,
    accords: List[str] | None,
) -> float:
    """
    날씨 기반 보정값 (별도 점수가 아니라 보정용 weight)
    대략 -0.2 ~ +0.2 범위에서 움직이도록 제한.
    """
    if accords is None:
        accords = []
    acc_set = set(accords)

    boost = 0.0

    # 더운 날씨: 시원/상쾌 계열 ↑, 무거운/달달 계열 ↓
    if temp >= 26:
        if {"citrus", "green", "aquatic"}.intersection(acc_set):
            boost += 0.15
        if {"amber", "sweet", "vanilla", "spicy"}.intersection(acc_set):
            boost -= 0.10

    # 추운 날씨: 우디/앰버/스파이시 계열 ↑, 너무 상큼한 계열 ↓
    elif temp <= 8:
        if {"amber", "woody", "spicy", "vanilla"}.intersection(acc_set):
            boost += 0.15
        if {"citrus", "green", "aquatic"}.intersection(acc_set):
            boost -= 0.05

    # 습도 높을 때: 너무 달달/파우더리 ↓, 깨끗/시트러스 ↑
    if humidity >= 70:
        if {"citrus", "green"}.intersection(acc_set):
            boost += 0.05
        if {"sweet", "gourmand", "powdery"}.intersection(acc_set):
            boost -= 0.05

    # 안전 범위로 클램핑
    if boost > 0.2:
        boost = 0.2
    if boost < -0.2:
        boost = -0.2

    # -0.2 ~ +0.2 -> 0 ~ 1 로 리스케일
    normalized = (boost + 0.2) / 0.4
    return float(normalized)


# ---------------------------------------------------------------------
# 오늘의 맞춤 추천 API
#   - 로그인 O: 사용자 선호도 + 계절 + 날씨 + 상황
#   - 로그인 X: 계절 + 날씨 + 상황(사용자 선호도 비중 0 으로 처리)
# ---------------------------------------------------------------------
@router.get("/today")
async def recommend_today(
    occasion: str = Query(
        ...,
        description="오늘의 상황: professional | casual | nightout",
    ),
    lat: float = Query(..., description="사용자 위도"),
    lon: float = Query(..., description="사용자 경도"),
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_id),
):
    # 1. occasion 검증
    if occasion not in ("professional", "casual", "nightout"):
        raise HTTPException(status_code=400, detail="invalid occasion")

    # 2. 날씨 정보 호출
    weather = await fetch_weather(lat, lon, settings.OPENWEATHER_API_KEY)
    temp = float(weather["main"]["temp"])
    humidity = int(weather["main"]["humidity"])
    condition = weather["weather"][0]["main"]
    dt_utc = int(weather.get("dt", 0))

    # 3. 날짜 + 위도 기반 계절 판단, temp 로 가중치 미세 조정
    season = detect_season_from_date(lat, dt_utc)
    weight_override = adjust_weights_by_temp(season, temp)

    # 4. 로그인 유저라면 취향 프로필 가져오기
    user_pref = None
    is_guest = current_user is None
    if not is_guest:
        # user_preference 가 없으면 내부에서 계산 후 upsert 해주는 함수라고 가정
        user_pref = get_or_build_user_preference(db, current_user.id)

    pref_accords_map: Dict[str, float] = {}
    if user_pref is not None and getattr(user_pref, "preferred_accords", None):
        pref_accords_map = _normalize_pref_accords(user_pref.preferred_accords)

    # 5. 추천 후보 향수 로딩 (너무 많으면 부담이니 상위 N개만)
    #    정렬 기준은 아무거나 가능. 여기서는 일단 인기순 + id 역순.
    candidates: List[Perfume] = (
        db.query(Perfume)
        .order_by(Perfume.view_count.desc(), Perfume.id.desc())
        .limit(400)
        .all()
    )

    results: List[Dict[str, Any]] = []

    for p in candidates:
        # 5-1. 계절 점수
        season_scores = season_score_map(p.season_ranking)
        _, _, stability, season_score = _calc_season_score(
            season,
            season_scores,
            weight_override,
        )

        # 5-2. 상황 점수
        occ_scores = _parse_occasion_scores(p.occasion_ranking)
        occasion_score = occ_scores.get(occasion, 0.0)

        # 5-3. 취향 유사도 (비로그인 = 0)
        pref_sim = 0.0
        if pref_accords_map:
            pref_sim = _accord_similarity(
                pref_accords_map,
                p.main_accords or [],
            )

        # 5-4. 날씨 보정 점수
        weather_boost = _calc_weather_boost(
            temp=temp,
            humidity=humidity,
            accords=p.main_accords or [],
        )

        # 5-5. 최종 점수 계산
        #   - 로그인 유저: pref_sim 이 0~1
        #   - 비로그인 유저: pref_sim = 0 이라서 자연스럽게 "사용자 선호도 비중 제외"
        final_score = (
            0.55 * pref_sim
            + 0.25 * float(season_score)
            + 0.15 * float(occasion_score)
            + 0.05 * float(weather_boost)
        )

        results.append(
            {
                "id": uuid_bytes_to_hex(p.id),
                "name": p.name,
                "brand_name": p.brand_name,
                "image_url": p.image_url,
                "gender": p.gender,
                "score": round(float(final_score), 3),
            }
        )

    # 6. 점수 기준 내림차순 정렬 후 limit 만큼 잘라내기
    results.sort(key=lambda x: x["score"], reverse=True)
    items = results[:limit]

    # 7. 응답
    return {
        "context": {
            "occasion": occasion,
            "season": season,
            "is_guest": is_guest,
            "weather": {
                "temp": temp,
                "humidity": humidity,
                "condition": condition,
            },
        },
        "items": items,
    }













@router.get(
    "/recent-views",
    response_model=RecentViewedList,
    summary="최근 본 향수 목록 (최대 7개)",
)
def recent_viewed_perfumes(
    limit: int = 7,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_id),
):
    """
    로그인한 사용자의 최근 본 향수 목록을 반환한다.
    - 최근 본 순서(viewed_at DESC)
    - 최대 limit개 (기본 7개)
    - 비로그인 사용자는 401
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="로그인 필요")

    # user_id bytes 추출
    if hasattr(current_user, "id"):
        user_id_bytes: bytes = current_user.id
    elif isinstance(current_user, bytes):
        user_id_bytes = current_user
    else:
        raise HTTPException(status_code=400, detail="invalid user object")

    # RecentView 와 Perfume join 해서 정보 한 번에 로딩
    rows = (
        db.query(RecentView, Perfume)
        .join(Perfume, RecentView.perfume_id == Perfume.id)
        .filter(RecentView.user_id == user_id_bytes)
        .order_by(RecentView.viewed_at.desc())
        .limit(limit)
        .all()
    )

    items: list[RecentViewedPerfume] = []
    for rv, p in rows:
        items.append(
            RecentViewedPerfume(
                perfume_id=uuid_bytes_to_hex(p.id),
                name=p.name,
                brand_name=p.brand_name,
                image_url=p.image_url,
                gender=p.gender,
                viewed_at=rv.viewed_at,
            )
        )

    return RecentViewedList(items=items)
