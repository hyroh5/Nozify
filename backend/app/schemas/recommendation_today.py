# app/schemas/recommendation_today.py
from typing import List, Optional
from pydantic import BaseModel


class TodayWeather(BaseModel):
    temp: float
    humidity: int
    condition: str


class TodayContext(BaseModel):
    season: str
    occasion: str
    weather: Optional[TodayWeather] = None


class TodayRecommendationItem(BaseModel):
    perfume_id: str
    name: str
    brand_name: str
    image_url: Optional[str] = None
    score: float
    reason: str


class TodayRecommendationResponse(BaseModel):
    context: TodayContext
    items: List[TodayRecommendationItem]
