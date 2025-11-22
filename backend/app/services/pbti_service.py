# backend/app/services/pbti_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.pbti_question import PBTIQuestion
from app.models.pbti_result import PBTIResult
from app.models.pbti_recommendation import PBTIRecommendation

from app.schemas.pbti import PBTISubmitRequest


# -------------------------------
# 질문 목록 가져오기
# -------------------------------
def get_questions(db: Session):
    questions = (
        db.query(PBTIQuestion)
        .filter(PBTIQuestion.active == True)
        .order_by(PBTIQuestion.id.asc())
        .all()
    )

    if not questions:
        raise HTTPException(status_code=500, detail="PBTI 질문이 DB에 없습니다.")

    return questions


# -------------------------------
# 답변 제출 + 결과 계산 + 저장
# -------------------------------
def submit_answers_and_make_result(db: Session, user_id_hex: str, body: PBTISubmitRequest):
    # 1 질문 로드
    questions = get_questions(db)

    # 2 답변 개수 검증
    if len(body.answers) != len(questions):
        raise HTTPException(status_code=400, detail="답변 개수가 질문 개수와 다릅니다.")

    # 3 점수 계산 (category, weight 기반)
    axis_scores = {}
    qmap = {q.id: q for q in questions}

    for ans in body.answers:
        q = qmap.get(ans.question_id)
        if not q:
            raise HTTPException(status_code=400, detail=f"잘못된 question_id: {ans.question_id}")

        axis = q.category  # ex) warm, fresh, heavy, light ...
        weight = q.weight or 1

        axis_scores[axis] = axis_scores.get(axis, 0) + (ans.choice - 3) * weight

    # 4 type_code 계산 (예시 로직)
    warm = axis_scores.get("warm", 0)
    fresh = axis_scores.get("fresh", 0)
    heavy = axis_scores.get("heavy", 0)
    light = axis_scores.get("light", 0)

    first = "warm" if warm >= fresh else "fresh"
    second = "heavy" if heavy >= light else "light"
    type_code = f"{first}-{second}"

    # 5 결과 저장
    new_result = PBTIResult(
        user_id=bytes.fromhex(user_id_hex),
        type_code=type_code,
        scores=axis_scores,
    )

    db.add(new_result)
    db.commit()
    db.refresh(new_result)

    # 6 응답
    return {
        "result_id": new_result.id,
        "user_id": user_id_hex,
        "type_code": type_code,
        "scores": axis_scores,
        "created_at": str(new_result.created_at),
    }


# -------------------------------
# 특정 결과 조회
# -------------------------------
def get_result_by_id(db: Session, result_id: int, user_id_hex: str):
    return (
        db.query(PBTIResult)
        .filter(
            PBTIResult.id == result_id,
            PBTIResult.user_id == bytes.fromhex(user_id_hex),
        )
        .first()
    )


# -------------------------------
# 추천 조회
# -------------------------------
def get_recommendations_by_type(db: Session, type_code: str):
    recs = (
        db.query(PBTIRecommendation)
        .filter(PBTIRecommendation.type_code == type_code)
        .all()
    )

    return {
        "type_code": type_code,
        "perfumes": [
            {
                "perfume_id": r.perfume_id,
                "name": r.perfume.name,
                "brand": r.perfume.brand.name,
                "image_url": r.perfume.image_url,
                "match_score": r.match_score,
            }
            for r in recs
        ],
    }
