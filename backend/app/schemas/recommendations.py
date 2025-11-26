# app/schemas/recommendations.py

from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional


class RecentViewedPerfume(BaseModel):
    perfume_id: str
    name: str
    brand_name: str
    image_url: Optional[str] = None
    gender: Optional[str] = None
    viewed_at: datetime


class RecentViewedList(BaseModel):
    items: List[RecentViewedPerfume]

class PBTIHomeItem(BaseModel):
    perfume_id: str
    name: str
    brand_name: str
    image_url: Optional[str] = None
    score: float


class PBTIHomeResponse(BaseModel):
    final_type: str
    tags: List[str]          # ["Warm", "Heavy"] 이런 식
    phrase: str              # "Warm · Heavy한 당신에게 어울리는 향이에요"
    items: List[PBTIHomeItem]