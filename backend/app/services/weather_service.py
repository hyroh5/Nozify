from typing import Dict, Any
import httpx

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


def detect_season_from_temp(temp: float) -> str:
    if temp <= 5:
        return "winter"
    if temp <= 15:
        return "fall"
    if temp <= 23:
        return "spring"
    return "summer"
