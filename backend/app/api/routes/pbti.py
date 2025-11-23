import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List, Tuple, Any

from app.core.db import get_db
from app.api.deps import get_current_user_id
from app.models.pbti_question import PBTIQuestion
from app.models.pbti_result import PBTIResult
from app.models.user import User

from app.models.perfume import Perfume
from app.models.brand import Brand

from app.services.recommendation_service import get_pbti_recommendations_by_type

from app.schemas.pbti import (
    PBTISubmitRequest,
    PBTISubmitResponse,
    PBTIResultResponse,
    PBTIRecommendationsResponse,
    PBTIRecommendationItem,
)

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pbti", tags=["pbti"])

# 질문 메타 dim reverse
QUESTION_META: Dict[int, Tuple[int, bool]] = {
    1: (1, False), 2: (1, True), 3: (1, False), 4: (1, True), 5: (1, False), 6: (1, True),
    7: (2, False), 8: (2, True), 9: (2, False), 10: (2, True), 11: (2, False), 12: (2, True),
    13: (3, False), 14: (3, True), 15: (3, False), 16: (3, True), 17: (3, True), 18: (3, False),
    19: (4, False), 20: (4, True), 21: (4, False), 22: (4, True), 23: (4, False), 24: (4, True),
}

DIMENSION_LETTERS = {
    1: ("F", "W"),
    2: ("L", "H"),
    3: ("S", "P"),
    4: ("N", "M"),
}

TYPE_NAMES = {}


def choice_to_score(choice: int) -> int:
    return choice - 3


def normalize_score(raw_sum: int, n_items: int) -> int:
    min_sum = -2 * n_items
    max_sum = 2 * n_items
    norm = (raw_sum - min_sum) / (max_sum - min_sum) * 100
    return int(round(norm))


def calc_confidence(raw_sum: int, n_items: int) -> float:
    return abs(raw_sum) / (2 * n_items)


def _format_result_response(r: PBTIResult) -> PBTIResultResponse:
    raw_sum = {1: 0, 2: 0, 3: 0, 4: 0}
    cnt = {1: 0, 2: 0, 3: 0, 4: 0}

    for a in (r.answers or []):
        qid = a.get("question_id")
        score = a.get("score")
        if qid in QUESTION_META and isinstance(score, int):
            dim, _ = QUESTION_META[qid]
            raw_sum[dim] += score
            cnt[dim] += 1

    confs = [
        calc_confidence(raw_sum[d], cnt[d]) if cnt[d] > 0 else 0.0
        for d in [1, 2, 3, 4]
    ]
    confidence = float(round(sum(confs) / 4.0, 3))

    return PBTIResultResponse(
        temperature_score=r.temperature_score or 0,
        texture_score=r.texture_score or 0,
        mood_score=r.mood_score or 0,
        nature_score=r.nature_score or 0,
        final_type=r.final_type or "",
        type_name=r.type_name or (r.final_type or ""),
        confidence=confidence,
        answers=r.answers or [],
    )


def calculate_match_score(user_scores: Dict[str, int], perfume_scores: Dict[str, float]) -> float:
    user_centered = {
        "F_W_Score": user_scores["temperature_score"] * 2 - 100,
        "L_H_Score": user_scores["texture_score"] * 2 - 100,
        "S_P_Score": user_scores["mood_score"] * 2 - 100,
        "N_M_Score": user_scores["nature_score"] * 2 - 100,
    }

    diff_sum = 0.0
    perfume_keys = ["F_W_Score", "L_H_Score", "S_P_Score", "N_M_Score"]
    user_keys = list(user_centered.keys())

    for u_key, p_key in zip(user_keys, perfume_keys):
        diff_sum += abs(user_centered[u_key] - (perfume_scores[p_key] or 0.0))

    max_diff_sum = 800.0
    match_score = 1.0 - (diff_sum / max_diff_sum)
    return max(0.0, min(1.0, float(round(match_score, 3))))


@router.get("/questions")
def get_questions(db: Session = Depends(get_db)):
    qs = (
        db.query(PBTIQuestion)
        .filter(PBTIQuestion.active == True)
        .order_by(PBTIQuestion.id.asc())
        .all()
    )
    return [
        {
            "id": q.id,
            "axis": q.axis,
            "direction": q.direction,
            "text": q.text,
            "active": q.active,
        }
        for q in qs
    ]


@router.post("/submit", response_model=PBTISubmitResponse, status_code=status.HTTP_201_CREATED)
def submit_pbti(
    body: PBTISubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
):
    current_user_id_bytes = current_user.id

    if not body.answers:
        raise HTTPException(status_code=400, detail="answers가 비어있습니다")

    raw_sum = {1: 0, 2: 0, 3: 0, 4: 0}
    cnt = {1: 0, 2: 0, 3: 0, 4: 0}
    packed_answers: List[dict] = []

    for a in body.answers:
        if a.question_id not in QUESTION_META:
            raise HTTPException(status_code=400, detail=f"unknown question_id {a.question_id}")

        dim, is_reverse = QUESTION_META[a.question_id]
        s = choice_to_score(a.choice)
        if is_reverse:
            s = -s

        raw_sum[dim] += s
        cnt[dim] += 1
        packed_answers.append({"question_id": a.question_id, "choice": a.choice, "score": s})

    dim_scores = {}
    dim_conf = {}
    for d in [1, 2, 3, 4]:
        if cnt[d] == 0:
            raise HTTPException(status_code=400, detail=f"dimension {d} answers missing")
        dim_scores[d] = normalize_score(raw_sum[d], cnt[d])
        dim_conf[d] = calc_confidence(raw_sum[d], cnt[d])

    letters = []
    for d in [1, 2, 3, 4]:
        left, right = DIMENSION_LETTERS[d]
        letters.append(left if dim_scores[d] >= 50 else right)

    final_type = "".join(letters)
    type_name = TYPE_NAMES.get(final_type, final_type)
    confidence = float(round(sum(dim_conf.values()) / 4.0, 3))

    db.query(PBTIResult).filter(
        PBTIResult.user_id == current_user_id_bytes,
        PBTIResult.is_active == True,
    ).update({"is_active": False}, synchronize_session="fetch")

    new_result = PBTIResult(
        user_id=current_user_id_bytes,
        temperature_score=dim_scores[1],
        texture_score=dim_scores[2],
        mood_score=dim_scores[3],
        nature_score=dim_scores[4],
        final_type=final_type,
        type_name=type_name,
        answers=packed_answers,
        is_active=True,
    )
    db.add(new_result)
    db.commit()
    db.refresh(new_result)

    return PBTISubmitResponse(
        temperature_score=dim_scores[1],
        texture_score=dim_scores[2],
        mood_score=dim_scores[3],
        nature_score=dim_scores[4],
        final_type=final_type,
        type_name=type_name,
        confidence=confidence,
        answers=packed_answers,
    )


@router.get("/result", response_model=PBTIResultResponse)
def get_my_pbti_result(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
):
    current_user_id_bytes = current_user.id

    r = (
        db.query(PBTIResult)
        .filter(PBTIResult.user_id == current_user_id_bytes, PBTIResult.is_active == True)
        .order_by(PBTIResult.created_at.desc())
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="active pbti result not found")

    return _format_result_response(r)


@router.get("/history", response_model=List[PBTIResultResponse])
def get_all_pbti_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
):
    current_user_id_bytes = current_user.id

    results = (
        db.query(PBTIResult)
        .filter(PBTIResult.user_id == current_user_id_bytes)
        .order_by(PBTIResult.created_at.desc())
        .all()
    )

    if not results:
        return []

    return [_format_result_response(r) for r in results]


@router.get("/recommendations", response_model=PBTIRecommendationsResponse)
def recommend_by_pbti(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
    limit: int = 10,
):
    current_user_id_bytes = current_user.id

    user_result = (
        db.query(PBTIResult)
        .filter(PBTIResult.user_id == current_user_id_bytes, PBTIResult.is_active == True)
        .order_by(PBTIResult.created_at.desc())
        .first()
    )
    if not user_result:
        raise HTTPException(status_code=404, detail="active pbti result not found for user")

    final_type = user_result.final_type or ""

    user_pbti_scores = {
        "temperature_score": user_result.temperature_score or 50,
        "texture_score": user_result.texture_score or 50,
        "mood_score": user_result.mood_score or 50,
        "nature_score": user_result.nature_score or 50,
    }

    try:
        perfume_rows = (
            db.query(
                Perfume.id,
                Perfume.name,
                Perfume.F_W_Score,
                Perfume.L_H_Score,
                Perfume.S_P_Score,
                Perfume.N_M_Score,
                Brand.name.label("brand_name"),
            )
            .join(Brand, Perfume.brand_id == Brand.id)
            .all()
        )
    except Exception as e:
        logger.error(f"Database Query Error on Perfume Profile: {e}")
        raise HTTPException(status_code=500, detail="향수 프로파일 데이터를 가져오는 중 오류가 발생했습니다")

    if not perfume_rows:
        return PBTIRecommendationsResponse(final_type=final_type, items=[])

    scored_perfumes: List[Dict[str, Any]] = []
    skipped_count = 0

    for row in perfume_rows:
        perfume_pbti_scores = {
            "F_W_Score": row.F_W_Score or 0.0,
            "L_H_Score": row.L_H_Score or 0.0,
            "S_P_Score": row.S_P_Score or 0.0,
            "N_M_Score": row.N_M_Score or 0.0,
        }

        match_score = calculate_match_score(user_pbti_scores, perfume_pbti_scores)

        raw_perfume_id = row.id
        try:
            if isinstance(raw_perfume_id, bytes) and len(raw_perfume_id) == 16:
                perfume_id_safe = str(uuid.UUID(bytes=raw_perfume_id))
            elif isinstance(raw_perfume_id, str):
                perfume_id_safe = raw_perfume_id
            else:
                perfume_id_safe = str(raw_perfume_id)
        except Exception as e:
            logger.error(f"Perfume ID conversion failed for ID: {raw_perfume_id!r}. Error: {e}")
            skipped_count += 1
            continue

        scored_perfumes.append({
            "perfume_id": perfume_id_safe,
            "name": row.name,
            "brand_name": row.brand_name,
            "score": match_score,
        })

    if skipped_count > 0:
        logger.warning(f"{skipped_count} items skipped due to ID conversion errors")

    scored_perfumes.sort(key=lambda x: x["score"], reverse=True)
    top_recommendations = scored_perfumes[:limit]

    items: List[PBTIRecommendationItem] = [
        PBTIRecommendationItem(
            perfume_id=p["perfume_id"],
            name=p["name"],
            brand_name=p["brand_name"],
            score=p["score"],
        )
        for p in top_recommendations
    ]

    return PBTIRecommendationsResponse(final_type=final_type, items=items)


@router.get("/recommendations/by_type")
def recommend_by_pbti_type(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
    limit: int = 10,
):
    current_user_id_bytes = current_user.id

    user_result = (
        db.query(PBTIResult)
        .filter(PBTIResult.user_id == current_user_id_bytes, PBTIResult.is_active == True)
        .order_by(PBTIResult.created_at.desc())
        .first()
    )
    if not user_result:
        raise HTTPException(status_code=404, detail="active pbti result not found for user")

    final_type = user_result.final_type
    if not final_type or len(final_type) != 4:
        raise HTTPException(status_code=400, detail="Invalid or missing final_type in user result")

    try:
        recommendations = get_pbti_recommendations_by_type(db, final_type, limit=limit)
    except Exception as e:
        logger.error(f"Recommendation Service Error: {e}")
        raise HTTPException(status_code=500, detail="PBTI 유형 기반 추천 데이터를 가져오는 중 오류가 발생했습니다")

    formatted_recommendations: Dict[str, List[PBTIRecommendationItem]] = {}

    for category, perfumes in recommendations.items():
        formatted_list: List[PBTIRecommendationItem] = []
        for p in perfumes:
            raw_id = p["id"]
            try:
                if isinstance(raw_id, bytes) and len(raw_id) == 16:
                    safe_id = str(uuid.UUID(bytes=raw_id))
                elif isinstance(raw_id, str):
                    safe_id = raw_id
                else:
                    safe_id = str(raw_id)
            except Exception as e:
                logger.error(f"Error converting type-based perfume ID: {raw_id!r}. Error: {e}")
                continue

            formatted_list.append(
                PBTIRecommendationItem(
                    perfume_id=safe_id,
                    name=p["name"],
                    brand_name=p.get("brand"),
                    score=1.0,
                )
            )

        formatted_recommendations[category] = formatted_list

    return {
        "final_type": final_type,
        "recommendations_by_type": formatted_recommendations,
        "message": f"PBTI 타입 {final_type}에 대한 5가지 카테고리별 추천 결과입니다",
    }
