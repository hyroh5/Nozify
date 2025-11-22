# backend/app/schemas/pbti.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# =========================
# 공통 입력 스키마
# =========================
class PBTIAnswerItem(BaseModel):
    question_id: int = Field(..., ge=1)
    choice: int = Field(..., ge=1, le=5)  # 1~5 리커트


class PBTISubmitRequest(BaseModel):
    answers: List[PBTIAnswerItem]


# =========================
# 제출 응답 스키마
# routes/pbti.py submit_pbti 반환과 일치
# =========================
class PBTISubmitResponse(BaseModel):
    temperature_score: int
    texture_score: int
    mood_score: int
    nature_score: int
    final_type: str
    type_name: str
    confidence: float
    answers: List[Dict[str, Any]]


# =========================
# 결과 조회 응답 스키마
# routes/pbti.py get_my_pbti_result 반환과 일치
# =========================
class PBTIResultResponse(BaseModel):
    temperature_score: int
    texture_score: int
    mood_score: int
    nature_score: int
    final_type: str
    type_name: str
    confidence: float
    answers: List[Dict[str, Any]]


# =========================
# 추천 응답 스키마
# routes/pbti.py recommend_by_pbti 반환과 일치
# =========================
class PBTIRecommendationItem(BaseModel):
    perfume_id: int
    name: str
    brand_name: Optional[str] = None
    score: float


class PBTIRecommendationsResponse(BaseModel):
    final_type: str
    items: List[PBTIRecommendationItem]
