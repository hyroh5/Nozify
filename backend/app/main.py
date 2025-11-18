# backend/app/main.py
from fastapi import FastAPI
from app.core.config import settings
from app.core.db import ping as db_ping
from app.api.v1.router import api_v1
from app.api.routes.health import router as health_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth

app = FastAPI(title="Nozify API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 배포 시 도메인으로 좁히기
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 헬스체크
@app.get("/health")
def health():
    return {"status": "ok", "db": db_ping()}

# v1 전체 라우터(prefix 적용)
app.include_router(api_v1, prefix=settings.API_PREFIX)
app.include_router(auth.router, prefix="/api/v1")