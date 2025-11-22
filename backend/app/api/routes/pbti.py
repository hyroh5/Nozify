from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.api.deps import get_current_user_id
from app.schemas.pbti import (
    PBTIQuestion,
    PBTISubmitRequest,
    PBTIResultResponse,
    PBTIRecommendationResponse
)
from app.services.pbti_service import (
    get_questions,
    submit_answers_and_make_result,
    get_result_by_id,
    get_recommendations_by_type
)

router = APIRouter(prefix="/pbti", tags=["pbti"])


# 1) 질문 목록 가져오기
@router.get("/questions", response_model=list[PBTIQuestion])
def read_questions(db: Session = Depends(get_db)):
    return get_questions(db)


# 2) 답변 제출하고 결과 생성
@router.post("/submit", response_model=PBTIResultResponse)
def submit_pbti(
    body: PBTISubmitRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    # body.answers 는 20개 들어온다고 가정
    # 질문 목록 없으면 서비스에서 에러 처리
    result = submit_answers_and_make_result(db, current_user_id, body)
    return result


# 3) 특정 결과 조회
@router.get("/result/{result_id}", response_model=PBTIResultResponse)
def read_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    result = get_result_by_id(db, result_id, current_user_id)
    if not result:
        raise HTTPException(status_code=404, detail="결과를 찾을 수 없습니다.")
    return result


# 4) 결과 기반 추천
@router.get("/recommendations/{type_code}", response_model=PBTIRecommendationResponse)
def read_recommendations(
    type_code: str,
    db: Session = Depends(get_db),
):
    return get_recommendations_by_type(db, type_code)
