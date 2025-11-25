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
