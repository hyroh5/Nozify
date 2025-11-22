from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.pbti_question import PBTIQuestion as PBTIQuestionModel
<<<<<<< Updated upstream
from app.models.pbti_result import PBTIResult as PBTIResultModel
from app.models.pbti_recommendation import PBTIRecommendation as PBTIRecommendationModel
=======
from app.models.pbti_result import PBtiResult as PBtiResultModel
from app.models.pbti_recommendation import PBtiRecommendation as PBtiRecommendationModel
>>>>>>> Stashed changes

from app.schemas.pbti import PBTISubmitRequest


def get_questions(db: Session):
<<<<<<< Updated upstream
    questions = db.query(PBTIQuestionModel).order_by(PBTIQuestionModel.id.asc()).all()
=======
    questions = db.query(PBTIQuestion)\
    .filter(PBTIQuestion.active == True)\
    .order_by(PBTIQuestion.axis.asc(), PBTIQuestion.id.asc())\
    .all()
>>>>>>> Stashed changes
    if not questions:
        raise HTTPException(status_code=500, detail="PBTI 질문이 DB에 없습니다.")
    return questions


def submit_answers_and_make_result(db: Session, user_id_hex: str, body: PBTISubmitRequest):
    # 1. 질문 로드
    questions = get_questions(db)

    # 2. 답변 개수 검증
    if len(body.answers) != len(questions):
        raise HTTPException(status_code=400, detail="답변 개수가 질문 개수와 다릅니다.")

    # 3. 점수 계산
    # 질문 테이블의 category, weight 기준으로 축 점수 합산
    axis_scores = {}
    qmap = {q.id: q for q in questions}

    for ans in body.answers:
        q = qmap.get(ans.question_id)
        if not q:
            raise HTTPException(status_code=400, detail=f"잘못된 question_id: {ans.question_id}")

        axis = q.category
        axis_scores[axis] = axis_scores.get(axis, 0) + ans.score * (q.weight or 1)

    # 4. type_code 계산
    # 예시 규칙. 실제 기준은 나중에 맞춰 바꾸면 됨
    warm = axis_scores.get("warm", 0)
    fresh = axis_scores.get("fresh", 0)
    heavy = axis_scores.get("heavy", 0)
    light = axis_scores.get("light", 0)

    first = "warm" if warm >= fresh else "fresh"
    second = "heavy" if heavy >= light else "light"
    type_code = f"{first}-{second}"

    # 5. 결과 저장
    new_result = PBTIResultModel(
        user_id=bytes.fromhex(user_id_hex),
        type_code=type_code,
        scores=axis_scores,
    )
    db.add(new_result)
    db.commit()
    db.refresh(new_result)

    # 6. 응답 변환
    return {
        "result_id": new_result.id,
        "user_id": user_id_hex,
        "type_code": type_code,
        "scores": axis_scores,
        "created_at": str(new_result.created_at),
    }


def get_result_by_id(db: Session, result_id: int, user_id_hex: str):
    return db.query(PBTIResultModel).filter(
        PBTIResultModel.id == result_id,
        PBTIResultModel.user_id == bytes.fromhex(user_id_hex),
    ).first()


def get_recommendations_by_type(db: Session, type_code: str):
    recs = db.query(PBTIRecommendationModel).filter(
        PBTIRecommendationModel.type_code == type_code
    ).all()

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
        ]
    }
