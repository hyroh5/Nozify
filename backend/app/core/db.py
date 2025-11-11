# backend/app/core/db.py
from __future__ import annotations
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

def _dsn() -> str:
    # 1순위: DATABASE_URL 직접 지정
    if settings.DATABASE_URL:
        return settings.DATABASE_URL
    # 2순위: 컴포넌트 조합
    driver = getattr(settings, "DB_DRIVER", "pymysql")  # 기본 pymysql
    return (
        f"mysql+{driver}://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        f"?charset=utf8mb4"
    )

engine = create_engine(
    _dsn(),
    pool_pre_ping=True,
    pool_recycle=3600,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
    future=True,
)

def get_db() -> Generator[Session, None, None]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def ping() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
