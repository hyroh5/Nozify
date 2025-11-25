from typing import Dict, List, Tuple, Any
import math
import uuid

from sqlalchemy.orm import Session
from app.models.perfume import Perfume
from app.models.brand import Brand

SEASONS = ["spring", "summer", "fall", "winter"]

ADJACENT_MAP: Dict[str, Tuple[str, str]] = {
    "spring": ("winter", "summer"),
    "summer": ("spring", "fall"),
    "fall": ("summer", "winter"),
    "winter": ("fall", "spring"),
}

DEFAULT_WEIGHTS: Dict[str, Dict[str, float]] = {
    "now": {"current": 1.0, "adj1": 0.0, "adj2": 0.0, "stability": 0.0},
    "transition": {"current": 1.0, "adj1": 0.3, "adj2": 0.2, "stability": 0.0},
    "stable": {"current": 0.7, "adj1": 0.15, "adj2": 0.15, "stability": 0.3},
}


def bytes_uuid_to_str(raw_id: Any) -> str:
    if isinstance(raw_id, bytes) and len(raw_id) == 16:
        return str(uuid.UUID(bytes=raw_id))
    return str(raw_id)


def season_score_map(season_ranking: Any) -> Dict[str, float]:
    if not season_ranking:
        return {s: 0.0 for s in SEASONS}

    m = {s: 0.0 for s in SEASONS}
    for item in season_ranking:
        name = item.get("name")
        score = item.get("score", 0.0)
        if name in m:
            m[name] = float(score or 0.0)
    return m


def calc_stability(scores: Dict[str, float]) -> float:
    vals = [scores[s] for s in SEASONS]
    mean = sum(vals) / 4.0
    var = sum((v - mean) ** 2 for v in vals) / 4.0
    std = math.sqrt(var)
    if std == 0:
        return 1.0
    return float(round(1.0 / std, 3))


def calc_final_score(season: str, scores: Dict[str, float], weights: Dict[str, float]):
    adj1, adj2 = ADJACENT_MAP[season]

    current = scores[season]
    a1 = scores[adj1]
    a2 = scores[adj2]
    stability = calc_stability(scores)

    base = (
        current * weights["current"]
        + a1 * weights["adj1"]
        + a2 * weights["adj2"]
    )

    final_score = base * 0.7 + stability * weights["stability"]

    return current, base, stability, float(round(final_score, 3))


def make_comment(season: str, scores: Dict[str, float], stability: float) -> str:
    ranked = sorted(SEASONS, key=lambda s: scores[s], reverse=True)
    top = ranked[0]
    second = ranked[1]

    if top == season:
        return "지금 계절 점수가 가장 높아 제철에 잘 맞는 향입니다"
    adj1, _ = ADJACENT_MAP[season]
    if top == adj1 and second == season:
        return "환절기까지 자연스럽게 이어 쓰기 좋은 계절형입니다"
    if stability >= 1.0:
        return "특정 계절에 치우치지 않아 데일리로 쓰기 좋습니다"
    return "현재 계절에 무난하게 잘 어울리는 타입입니다"


def get_seasonal_perfumes(
    db: Session,
    season: str,
    mode: str,
    limit: int,
    offset: int,
    include_comment: bool = True,
    weights_override: Dict[str, float] | None = None
) -> List[Dict[str, Any]]:

    # mode 기반 기본 가중치 불러오고, override가 있으면 덮어쓰기
    weights = DEFAULT_WEIGHTS.get(mode, DEFAULT_WEIGHTS["transition"]).copy()
    if weights_override:
        weights.update(weights_override)

    rows = (
        db.query(
            Perfume.id,
            Perfume.name,
            Perfume.image_url,
            Perfume.gender,
            Perfume.season_ranking,
            Brand.name.label("brand_name"),
        )
        .join(Brand, Perfume.brand_id == Brand.id)
        .offset(offset)
        .limit(limit * 5)
        .all()
    )

    scored: List[Dict[str, Any]] = []
    for r in rows:
        scores = season_score_map(r.season_ranking)
        current, base, stability, final_score = calc_final_score(season, scores, weights)
        comment = make_comment(season, scores, stability) if include_comment else None

        scored.append({
            "perfume_id": bytes_uuid_to_str(r.id),
            "name": r.name,
            "brand_name": r.brand_name,
            "image_url": r.image_url,
            "gender": r.gender,
            "season_score": float(round(current, 3)),
            "final_score": final_score,
            "comment": comment,
        })

    scored.sort(key=lambda x: x["final_score"], reverse=True)
    return scored[:limit]
