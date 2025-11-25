# app/services/user_preference_service.py

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple, Optional

from sqlalchemy.orm import Session

from app.models.user_preference import UserPreference
from app.models.recent_view import RecentView
from app.models.wishlist import Wishlist
from app.models.purchase_history import PurchaseHistory
from app.models.perfume import Perfume

# 최근/위시/보유에 따른 가중치
WEIGHTS: Dict[str, float] = {
    "recent": 1.0,   # 최근 본 향수
    "wish": 3.0,     # 위시리스트
    "owned": 5.0,    # 실제 보유(구매)
}

# user_preference를 언제 “다시 계산할지” 기준 일수
STALE_DAYS = 7


# ---------------------------------------------------------
# 내부 유틸: 향수 하나를 취향 점수에 누적
# ---------------------------------------------------------
def _accumulate_from_perfume(
    perfume: Optional[Perfume],
    weight: float,
    accords_score: Dict[str, float],
    brand_score: Dict[str, float],
    prices: List[float],
    season_score: Dict[str, float],
    occasion_score: Dict[str, float],
) -> None:
    """Perfume 한 개의 정보를 사용자 취향 점수에 누적."""
    if perfume is None:
        return

    # 1) 어코드 점수
    # main_accords: ["sweet", "woody", ...] 형태라고 가정
    if perfume.main_accords:
        for acc in perfume.main_accords:
            if not acc:
                continue
            accords_score[str(acc)] += weight

    # 2) 브랜드 점수
    # v1: brand_name 기준으로 취향을 계산 (필요하면 brand_id로 바꿀 수 있음)
    if perfume.brand_name:
        brand_score[perfume.brand_name] += weight

    # 3) 가격 분포
    if perfume.price is not None:
        prices.append(float(perfume.price))

    # 4) 계절 선호 점수
    # season_ranking: [{"name": "spring", "score": 0.8}, ...]
    if perfume.season_ranking:
        for item in perfume.season_ranking:
            name = item.get("name")
            sc = item.get("score", 0.0)
            if not name:
                continue
            season_score[str(name)] += float(sc) * weight

    # 5) 상황(occasion) 선호 점수
    # occasion_ranking: [{"name": "casual", "score": 0.7}, ...] 라고 가정
    if hasattr(perfume, "occasion_ranking") and perfume.occasion_ranking:
        for item in perfume.occasion_ranking:
            name = item.get("name")
            sc = item.get("score", 0.0)
            if not name:
                continue
            occasion_score[str(name)] += float(sc) * weight


# ---------------------------------------------------------
# 1) 사용자 취향 계산 (메인 함수)
# ---------------------------------------------------------
def calculate_user_preference(db: Session, user_id: bytes) -> Dict[str, Any]:
    """
    recent_view, wishlist, purchase_history를 기반으로
    사용자 취향 프로필을 계산해서 dict로 반환.
    실제 DB 저장은 upsert_user_preference에서 수행.
    """
    accords_score: Dict[str, float] = defaultdict(float)
    brand_score: Dict[str, float] = defaultdict(float)
    prices: List[float] = []
    season_score: Dict[str, float] = defaultdict(float)
    occasion_score: Dict[str, float] = defaultdict(float)

    # 1) 최근 본 향수
    recent_views = db.query(RecentView).filter(RecentView.user_id == user_id).all()
    for rv in recent_views:
        perfume = db.get(Perfume, rv.perfume_id)
        _accumulate_from_perfume(
            perfume,
            WEIGHTS["recent"],
            accords_score,
            brand_score,
            prices,
            season_score,
            occasion_score,
        )

    # 2) 위시리스트
    wish_items = db.query(Wishlist).filter(Wishlist.user_id == user_id).all()
    for w in wish_items:
        perfume = db.get(Perfume, w.perfume_id)
        _accumulate_from_perfume(
            perfume,
            WEIGHTS["wish"],
            accords_score,
            brand_score,
            prices,
            season_score,
            occasion_score,
        )

    # 3) 구매/보유 향수
    purchased = db.query(PurchaseHistory).filter(PurchaseHistory.user_id == user_id).all()
    for ph in purchased:
        perfume = db.get(Perfume, ph.perfume_id)
        _accumulate_from_perfume(
            perfume,
            WEIGHTS["owned"],
            accords_score,
            brand_score,
            prices,
            season_score,
            occasion_score,
        )

    # ------------------------------------
    # 누적값을 정리해서 "선호 목록" 형태로 변환
    # ------------------------------------
    # 어코드 상위 N개
    preferred_accords = [
        name
        for name, _ in sorted(accords_score.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    # 브랜드 상위 N개 (v1: brand_name 기준)
    preferred_brands = [
        name
        for name, _ in sorted(brand_score.items(), key=lambda x: x[1], reverse=True)[:7]
    ]

    # 계절 상위 2개
    preferred_seasons = [
        name
        for name, _ in sorted(season_score.items(), key=lambda x: x[1], reverse=True)[:2]
    ]

    # 상황 상위 2개
    preferred_occasions = [
        name
        for name, _ in sorted(occasion_score.items(), key=lambda x: x[1], reverse=True)[:2]
    ]

    # 가격 범위 추정 (극단값 제거를 위해 분위수 사용)
    if prices:
        prices_sorted = sorted(prices)
        n = len(prices_sorted)
        lower_idx = max(0, n // 5)           # 약 20퍼센트 분위
        upper_idx = min(n - 1, n * 4 // 5)   # 약 80퍼센트 분위
        price_min = prices_sorted[lower_idx]
        price_max = prices_sorted[upper_idx]
    else:
        # 데이터 없으면 넓게 설정
        price_min, price_max = 0.0, 1_000_000.0

    return {
        "preferred_accords": preferred_accords,
        "preferred_brands": preferred_brands,
        "preferred_seasons": preferred_seasons,
        "preferred_occasions": preferred_occasions,
        "price_range_min": float(price_min),
        "price_range_max": float(price_max),
    }


# ---------------------------------------------------------
# 2) user_preference 테이블에 저장/업데이트
# ---------------------------------------------------------
def upsert_user_preference(db: Session, user_id: bytes, pref: Dict[str, Any]) -> UserPreference:
    row = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()

    if row is None:
        row = UserPreference(user_id=user_id)

    row.preferred_accords = pref.get("preferred_accords", [])
    row.preferred_brands = pref.get("preferred_brands", [])
    row.preferred_seasons = pref.get("preferred_seasons", [])
    row.preferred_occasions = pref.get("preferred_occasions", [])
    row.price_range_min = pref.get("price_range_min")
    row.price_range_max = pref.get("price_range_max")
    row.last_calculated_at = datetime.utcnow()

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# ---------------------------------------------------------
# 3) user_preference 가져오기 (+ 오래됐으면 자동 재계산)
# ---------------------------------------------------------
def get_user_preference(
    db: Session,
    user_id: bytes,
    auto_recalc: bool = True,
) -> Optional[UserPreference]:
    """
    - user_preference 레코드를 반환
    - 없거나 오래됐으면 calculate → upsert 후 다시 반환
    """
    row = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()

    need_recalc = False
    if row is None:
        need_recalc = True
    elif auto_recalc and row.last_calculated_at:
        if row.last_calculated_at < datetime.utcnow() - timedelta(days=STALE_DAYS):
            need_recalc = True

    if need_recalc and auto_recalc:
        pref_dict = calculate_user_preference(db, user_id)
        row = upsert_user_preference(db, user_id, pref_dict)

    return row


def get_or_build_user_preference(
    db: Session,
    user_id: bytes,
) -> Optional[UserPreference]:
    """
    1) user_preference 테이블에서 기존 기록을 먼저 찾고,
    2) 없으면 interaction 기반으로 새로 계산해서 upsert 한 뒤,
    3) 최종 UserPreference 객체를 반환한다.
    추천 API(recommendations_today)에서 이 함수만 쓰면 됨.
    """

    # 1. 이미 저장된 취향이 있는지 확인
    pref = get_user_preference(db, user_id)
    if pref is not None:
        return pref

    # 2. 없으면 interaction(최근 본 향수, 위시리스트, 구매내역 등) 기반으로 계산
    summary = calculate_user_preference(db, user_id)
    if summary is None:
        # 아직 본 향수/위시/구매가 전혀 없는 유저일 수도 있으므로 None 허용
        return None

    # 3. 계산된 요약을 user_preference 테이블에 저장(upsert)
    pref = upsert_user_preference(
        db=db,
        user_id=user_id,
        preferred_accords=summary.get("preferred_accords"),
        preferred_brands=summary.get("preferred_brands"),
        price_min=summary.get("price_min"),
        price_max=summary.get("price_max"),
        preferred_seasons=summary.get("preferred_seasons"),
        preferred_occasions=summary.get("preferred_occasions"),
    )
    return pref