from typing import Dict, Any
import httpx
from datetime import datetime

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"



async def fetch_weather(lat: float, lon: float, api_key: str) -> Dict[str, Any]:
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric"
    }
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.get(OPENWEATHER_URL, params=params)
        r.raise_for_status()
        return r.json()


# -------------------------------------------------------------------------
# 1) 날짜 기반 계절 판단 (기본 season)
# -------------------------------------------------------------------------
def detect_season_from_date(lat: float, dt_utc: int) -> str:
    """
    북반구/남반구 판단 후 날짜 기반 season 계산
    dt_utc: unix timestamp (openweather의 dt)
    """

    # 북반구/남반구 판단: 위도 기준
    northern = lat >= 0

    dt = datetime.utcfromtimestamp(dt_utc)
    month = dt.month

    if northern:
        # 북반구
        if month in (3, 4, 5):
            return "spring"
        if month in (6, 7, 8):
            return "summer"
        if month in (9, 10, 11):
            return "fall"
        return "winter"
    else:
        # 남반구: 반대
        if month in (3, 4, 5):
            return "fall"
        if month in (6, 7, 8):
            return "winter"
        if month in (9, 10, 11):
            return "spring"
        return "summer"


# -------------------------------------------------------------------------
# 2) temp 기반 가중치 보정 (season을 바꾸지 않고 weights만 조절)
# -------------------------------------------------------------------------
def adjust_weights_by_temp(base_season: str, temp: float) -> dict:
    """
    계절은 날짜 기반으로 유지하고,
    temp가 지나치게 높거나 낮으면 가중치를 미세하게 조정해준다.
    """

    # 기본값
    weights = {
        "current": 1.0,
        "adj1": 0.3,
        "adj2": 0.2,
        "stability": 0.1,
    }

    # 더운 날씨 → summer 비중 증가
    if temp >= 26:
        if base_season == "summer":
            weights["current"] = 1.2
        else:
            weights["adj2"] += 0.1  # summer 인접 계절 비중 증가

    # 추운 날씨 → winter 비중 증가
    elif temp <= 5:
        if base_season == "winter":
            weights["current"] = 1.2
        else:
            weights["adj1"] += 0.1  # winter 인접 계절 비중 증가

    return weights
