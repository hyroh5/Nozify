# backend/app/api/routes/pbti.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Tuple

from app.core.db import get_db
from app.api.deps import get_current_user_id
from app.models.pbti_question import PBTIQuestion
from app.models.pbti_result import PBTIResult

from app.schemas.pbti import (
    PBTISubmitRequest,
    PBTISubmitResponse,
    PBTIResultResponse,
    PBTIRecommendationsResponse,
    PBTIRecommendationItem,
)

router = APIRouter(prefix="/pbti", tags=["pbti"])

# ==================================================
# 질문 메타 (dim, reverse)
# ==================================================
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


# ==================================================
# 유틸 함수
# ==================================================
def choice_to_score(choice: int) -> int:
    return choice - 3

def normalize_score(raw_sum: int, n_items: int) -> int:
    min_sum = -2 * n_items
    max_sum = 2 * n_items
    norm = (raw_sum - min_sum) / (max_sum - min_sum) * 100
    return int(round(norm))

def calc_confidence(raw_sum: int, n_items: int) -> float:
    return abs(raw_sum) / (2 * n_items)


# ==================================================
# GET /pbti/questions
# ==================================================
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


# ==================================================
# POST /pbti/submit
# ==================================================
@router.post("/submit", response_model=PBTISubmitResponse)
def submit_pbti(
    body: PBTISubmitRequest,
    db: Session = Depends(get_db),
    current_user_id: bytes = Depends(get_current_user_id),
):

    if not body.answers:
        raise HTTPException(status_code=400, detail="answers가 비어있습니다")

    # dim 별 점수
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

    # dim별 정규화
    dim_scores = {}
    dim_conf = {}
    for d in [1, 2, 3, 4]:
        if cnt[d] == 0:
            raise HTTPException(status_code=400, detail=f"dimension {d} answers missing")
        dim_scores[d] = normalize_score(raw_sum[d], cnt[d])
        dim_conf[d] = calc_confidence(raw_sum[d], cnt[d])

    # PBTI type
    letters = []
    for d in [1, 2, 3, 4]:
        left, right = DIMENSION_LETTERS[d]
        letters.append(left if dim_scores[d] >= 50 else right)

    final_type = "".join(letters)
    type_name = TYPE_NAMES.get(final_type, final_type)
    confidence = float(round(sum(dim_conf.values()) / 4.0, 3))

    # 이전 active 비활성화
    db.query(PBTIResult).filter(
        PBTIResult.user_id == current_user_id,
        PBTIResult.is_active == True,
    ).update({"is_active": False})

    # 새 결과 저장
    new_result = PBTIResult(
        user_id=current_user_id,
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


# ==================================================
# GET /pbti/result
# ==================================================
@router.get("/result", response_model=PBTIResultResponse)
def get_my_pbti_result(
    db: Session = Depends(get_db),
    current_user_id: bytes = Depends(get_current_user_id),
):
    r = (
        db.query(PBTIResult)
        .filter(PBTIResult.user_id == current_user_id, PBTIResult.is_active == True)
        .order_by(PBTIResult.created_at.desc())
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="active pbti result not found")

    # confidence 재계산
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


# ==================================================
# GET /pbti/recommendations
# ==================================================
@router.get("/recommendations", response_model=PBTIRecommendationsResponse)
def recommend_by_pbti(
    db: Session = Depends(get_db),
    current_user_id: bytes = Depends(get_current_user_id),
    limit: int = 10,
):
    r = (
        db.query(PBTIResult)
        .filter(PBTIResult.user_id == current_user_id, PBTIResult.is_active == True)
        .order_by(PBTIResult.created_at.desc())
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="active pbti result not found")

    final_type = r.final_type or ""
    items: List[PBTIRecommendationItem] = []

    # 1) monthly_perfume 테이블 기반 추천
    try:
        from app.models.monthly_perfume import MonthlyPerfume
        from app.models.perfume import Perfume
        from app.models.brand import Brand

        rows = (
            db.query(MonthlyPerfume, Perfume, Brand)
            .join(Perfume, MonthlyPerfume.perfume_id == Perfume.id)
            .join(Brand, Perfume.brand_id == Brand.id)
            .order_by(MonthlyPerfume.rank.asc())
            .limit(limit)
            .all()
        )

        for mp, p, b in rows:
            items.append(
                PBTIRecommendationItem(
                    perfume_id=p.id,
                    name=p.name,
                    brand_name=b.name,
                    score=float(1.0 / (mp.rank or 1)),
                )
            )

    except Exception:
        # 2) fallback: perfume 최신순
        try:
            from app.models.perfume import Perfume
            rows = db.query(Perfume).order_by(Perfume.id.desc()).limit(limit).all()
            for p in rows:
                items.append(
                    PBTIRecommendationItem(
                        perfume_id=p.id,
                        name=p.name,
                        brand_name=None,
                        score=0.0,
                    )
                )
        except Exception:
            items = []

    return PBTIRecommendationsResponse(final_type=final_type, items=items)
