# backend/app/schemas/pbti.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PBTIAnswerItem(BaseModel):
    question_id: int = Field(..., ge=1)
    choice: int = Field(..., ge=1, le=5)

<<<<<<< Updated upstream
<<<<<<< Updated upstream
class PBTIQuestion(BaseModel):
    id: int
    text: str
    axis: AxisType
    direction: int = Field(..., description="정방향 +1, 역방향 -1")
=======
class PBTISubmitRequest(BaseModel):
    answers: List[PBTIAnswerItem]
>>>>>>> Stashed changes
=======
class PBTISubmitRequest(BaseModel):
    answers: List[PBTIAnswerItem]
>>>>>>> Stashed changes

class PBTISubmitResponse(BaseModel):
    temperature_score: int
    texture_score: int
    mood_score: int
    nature_score: int
    final_type: str
    type_name: str
    confidence: float
    answers: List[Dict[str, Any]]

class PBTIResultResponse(BaseModel):
    temperature_score: int
    texture_score: int
    mood_score: int
    nature_score: int
    final_type: str
    type_name: str
    confidence: float
    answers: List[Dict[str, Any]]

<<<<<<< Updated upstream
<<<<<<< Updated upstream
class PBTISubmitRequest(BaseModel):
    answers: List[AnswerItem]
    owned_perfumes: Optional[List[int]] = None

class PBTIResult(BaseModel):
    temperature: int
    texture: int
    mood: int
    nature: int
    type_code: str

class PBTIResultResponse(BaseModel):
    result: PBTIResult

=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
class PBTIRecommendationItem(BaseModel):
    perfume_id: int
    name: str
    brand_name: Optional[str] = None
    score: float

<<<<<<< Updated upstream
<<<<<<< Updated upstream
class PBTIRecommendationResponse(BaseModel):
    type_code: str
    recommendations: List[PBTIRecommendationItem]
=======
class PBTIRecommendationsResponse(BaseModel):
    final_type: str
    items: List[PBTIRecommendationItem]
>>>>>>> Stashed changes
=======
class PBTIRecommendationsResponse(BaseModel):
    final_type: str
    items: List[PBTIRecommendationItem]
>>>>>>> Stashed changes
