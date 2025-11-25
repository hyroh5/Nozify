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

from app.services.seasonal_recommendation_service import get_seasonal_perfumes
from app.services.weather_service import (
    fetch_weather,
    detect_season_from_date,
    adjust_weights_by_temp
)

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

    items_raw = get_seasonal_perfumes(
        db, season, mode, limit, offset, include_comment
    )
    items = [SeasonalPerfumeItem(**x) for x in items_raw]

    return SeasonalPerfumeResponse(
        season=season, mode=mode, items=items
    )


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

    # 날짜 기반 season 먼저 결정
    base_season = detect_season_from_date(body.lat, weather["dt"])

    # temp 기반 weights 보정
    weights = adjust_weights_by_temp(base_season, temp)

    items_raw = get_seasonal_perfumes(
        db=db,
        season=base_season,
        mode="transition",
        limit=body.limit,
        offset=body.offset,
        include_comment=body.include_comment,
        weights_override=weights
    )

    items = [SeasonalPerfumeItem(**x) for x in items_raw]

    return WeatherSeasonalResponse(
        season_detected=base_season,
        weather_summary=WeatherSummary(
            temp=temp,
            feels_like=feels_like,
            humidity=humidity,
            condition=condition,
        ),
        weights=weights,
        items=items,
    )
