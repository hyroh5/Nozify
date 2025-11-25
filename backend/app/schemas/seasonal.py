from typing import List, Optional, Dict
from pydantic import BaseModel


class SeasonalPerfumeItem(BaseModel):
    perfume_id: str
    name: str
    brand_name: Optional[str] = None
    image_url: Optional[str] = None
    gender: Optional[str] = None
    season_score: float
    final_score: float
    comment: Optional[str] = None


class SeasonalPerfumeResponse(BaseModel):
    season: str
    mode: str
    items: List[SeasonalPerfumeItem]


class WeatherSeasonalRequest(BaseModel):
    lat: float
    lon: float
    limit: int = 20
    offset: int = 0
    include_comment: bool = True


class WeatherSummary(BaseModel):
    temp: float
    feels_like: float
    humidity: int
    condition: str


class WeatherSeasonalResponse(BaseModel):
    season_detected: str
    weather_summary: WeatherSummary
    weights: Dict[str, float]
    items: List[SeasonalPerfumeItem]
