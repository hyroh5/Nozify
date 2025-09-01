from __future__ import annotations

from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings


def _dsn() -> str:
    """
    SQLAlchemy용 MySQL DSN 생성.
    드라이버는 mysqlclient(=mysqldb)를 사용.
    """
    return (
        f"mysql+mysqldb://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        f"?charset=utf8mb4"
    )


# Engine: 커넥션 풀 포함
engine = create_engine(
    _dsn(),
    pool_pre_ping=True,     # 죽은 커넥션 자동 감지
    pool_recycle=3600,      # MySQL wait_timeout 대비(초)
    future=True,
)

# 요청 단위 세션 팩토리
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 의존성. 라우터 함수에서:
        def handler(db: Session = Depends(get_db)):
            ...
    처럼 주입 받아 사용.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ping() -> bool:
    """
    헬스체크 등에서 사용할 수 있는 간단한 DB 연결 테스트.
    예) /health 핸들러에서 호출해 상태 노출 가능.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
