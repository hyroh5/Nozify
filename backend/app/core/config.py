# app/core/config.py
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

import os
from dotenv import load_dotenv

load_dotenv()

# 프로젝트 루트 계산 (backend/ 기준으로 실행해도 안전)
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # .../app
ROOT_DIR = os.path.dirname(APP_DIR)                                     # .../backend

def _abs(path: str | None) -> str:
    if not path:
        return ""
    # 이미 절대경로면 그대로, 아니면 backend 기준 상대경로 → 절대경로
    return path if os.path.isabs(path) else os.path.join(ROOT_DIR, path)


class Settings(BaseSettings):
    APP_ENV: str = "dev"
    APP_NAME: str = "nozify-api"
    API_PREFIX: str = "/api/v1"

    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "nozify"
    DB_PASSWORD: str = "nozify_pw"
    DB_NAME: str = "nozify_db"

    DATABASE_URL: Optional[str] = None
    DB_DRIVER: str = "pymysql"

    # Fragella API 연동용 키
    FRAGELLA_API_KEY: Optional[str] = None

    # ★ 추가: OpenWeather API Key
    OPENWEATHER_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )



class VisionConfig:
    DEVICE = os.getenv("VISION_DEVICE", "cpu")
    MODEL_PATH = _abs(os.getenv("BOTTLE_MODEL_PATH", "backend/app/assets/models/perfume_seg.onnx"))

    OCR_LANGS = os.getenv("OCR_LANGS", "eng,kor")

    THRESH_BOTTLE_SCORE = float(os.getenv("THRESH_BOTTLE_SCORE", "0.5"))
    THRESH_TEXT_MATCH = float(os.getenv("THRESH_TEXT_MATCH", "0.7"))

    # 품질 임계(경험치, 필요시 조정)
    MIN_BLUR = float(os.getenv("MIN_BLUR", "30.0"))
    MIN_BRIGHTNESS = float(os.getenv("MIN_BRIGHTNESS", "0.15"))

    MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_BYTES", "3000000"))
    DEBUG_DIR = os.getenv("VISION_DEBUG_DIR", "backend/app/assets/debug")

    BOTTLE_MODEL_PT_PATH = _abs(os.getenv("BOTTLE_MODEL_PT_PATH", ""))

    # 사전 경로
    BRANDS_JSON = os.getenv("BRANDS_JSON", "backend/app/assets/dicts/brands.json")
    PRODUCTS_JSON = os.getenv("PRODUCTS_JSON", "backend/app/assets/dicts/products.json")


settings = Settings()
