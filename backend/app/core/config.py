from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "dev"
    APP_NAME: str = "nozify-api"
    API_PREFIX: str = "/api/v1"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "nozify"
    DB_PASSWORD: str = "nozify_pw"
    DB_NAME: str = "nozify_db"

    class Config:
        env_file = ".env"


# ✅ 여기서 settings라는 인스턴스를 만들어줘야 env.py에서 import 가능
settings = Settings()
