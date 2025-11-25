from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import settings

from app.schemas.seasonal import (
    SeasonalPerfumeResponse,
    WeatherSeasonalRequest,
    WeatherSeasonalResponse,
    SeasonalPerfumeItem,
    WeatherSummary,
)

from app.services.seasonal_recommendation_service import get_seasonal_perfumes, DEFAULT_WEIGHTS
from app.services.weather_service import fetch_weather, detect_season_from_temp

router = APIRouter(prefix="/catalog/seasonal", tags=["Seasonal"])


@router.get("/perfumes", response_model=SeasonalPerfumeResponse)
def seasonal_perfumes(
    season: str,
    mode: str = "transition",
    limit: int = 20,
    offset: int = 0,
    include_comment: bool = True,
    db: Session = Depends(get_db),
):
    if season not in ["spring", "summer", "fall", "winter"]:
        raise HTTPException(status_code=400, detail="invalid season")
    if mode not in ["now", "transition", "stable"]:
        raise HTTPException(status_code=400, detail="invalid mode")

    items_raw = get_seasonal_perfumes(db, season, mode, limit, offset, include_comment)
    items = [SeasonalPerfumeItem(**x) for x in items_raw]

    return SeasonalPerfumeResponse(season=season, mode=mode, items=items)


@router.post("/perfumes/weather", response_model=WeatherSeasonalResponse)
async def weather_seasonal_perfumes(
    body: WeatherSeasonalRequest,
    db: Session = Depends(get_db),
):
    weather = await fetch_weather(body.lat, body.lon, settings.OPENWEATHER_API_KEY)

    temp = float(weather["main"]["temp"])
    feels_like = float(weather["main"]["feels_like"])
    humidity = int(weather["main"]["humidity"])
    condition = weather["weather"][0]["main"]

    season_detected = detect_season_from_temp(temp)
    mode = "transition"

    items_raw = get_seasonal_perfumes(db, season_detected, mode, body.limit, body.offset, body.include_comment)
    items = [SeasonalPerfumeItem(**x) for x in items_raw]

    return WeatherSeasonalResponse(
        season_detected=season_detected,
        weather_summary=WeatherSummary(
            temp=temp,
            feels_like=feels_like,
            humidity=humidity,
            condition=condition,
        ),
        weights=DEFAULT_WEIGHTS[mode],
        items=items,
    )
