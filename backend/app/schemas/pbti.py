# backend/app/schemas/pbti.py

from typing import List, Optional, Dict
from pydantic import BaseModel


# ==========================================
# PBti 질문 스키마 (20문항 가정)
# ==========================================
class PBtiQuestion(BaseModel):
    id: int                    # 1~20
    text: str                  # 질문 내용
    category: str              # warm/fresh/heavy/light 등 축 구분
    weight: int = 1            # 점수 가중치 기본 1
    # 리커트 5점 척도 → choice_a/b 제거

    class Config:
        from_attributes = True


# ==========================================
# 답변 스키마 (5단계 척도)
# 1: 매우 그렇지 않다
# 2: 그렇지 않다
# 3: 보통이다
# 4: 그렇다
# 5: 매우 그렇다
# ==========================================
class PBtiAnswer(BaseModel):
    question_id: int
    score: int   # 1~5 (int)


class PBtiSubmitRequest(BaseModel):
    answers: List[PBtiAnswer]
    owned_perfumes: Optional[List[int]] = []  # 사용자가 보유한 향수 ID 리스트


# ==========================================
# 테스트 결과 반환
# ==========================================
class PBtiResultResponse(BaseModel):
    result_id: int
    user_id: str
    type_code: str               # 예: "warm-heavy", "fresh-light"
    scores: Dict[str, int]       # { warm: 12, fresh: 7, heavy: 15, light: 3 }
    created_at: str


# ==========================================
# 향수 추천 반환
# ==========================================
class PBtiPerfumeRecommendation(BaseModel):
    perfume_id: int
    name: str
    brand: str
    image_url: Optional[str]
    match_score: Optional[int] = 0


class PBtiRecommendationResponse(BaseModel):
    type_code: str
    perfumes: List[PBtiPerfumeRecommendation]
