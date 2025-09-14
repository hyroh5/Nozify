# app/core/config.py
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "dev"
    APP_NAME: str = "nozify-api"
    API_PREFIX: str = "/api/v1"

    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "nozify"
    DB_PASSWORD: str = "nozify_pw"
    DB_NAME: str = "nozify_db"

    # ✅ .env에 있는 이 키를 모델에 정의해야 함
    DATABASE_URL: Optional[str] = None

    # (선택) 드라이버 필드도 있으면 조립 시 편함
    DB_DRIVER: str = "pymysql"

    # ✅ pydantic v2 설정: .env 경로 + extra 무시
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # 알 수 없는 env 키 무시
    )


settings = Settings()

