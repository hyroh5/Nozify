# app/schemas/pbti.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

AxisType = Literal["temperature", "texture", "mood", "nature"]

class PBtiQuestion(BaseModel):
    id: int
    text: str
    axis: AxisType
    direction: int = Field(..., description="정방향 +1, 역방향 -1")

    class Config:
        from_attributes = True

class AnswerItem(BaseModel):
    question_id: int
    score: int = Field(..., ge=1, le=5, description="1 그렇지않다 ~ 5 매우그렇다")

class PBtiSubmitRequest(BaseModel):
    answers: List[AnswerItem]
    owned_perfumes: Optional[List[int]] = None

class PBtiResult(BaseModel):
    temperature: int
    texture: int
    mood: int
    nature: int
    type_code: str

class PBtiResultResponse(BaseModel):
    result: PBtiResult

class PBtiRecommendationItem(BaseModel):
    perfume_id: int
    name: str
    brand: str
    score: float

class PBtiRecommendationResponse(BaseModel):
    type_code: str
    recommendations: List[PBtiRecommendationItem]
