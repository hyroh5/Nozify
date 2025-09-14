# alembic/env.py — Nozify (MySQL, backend/app 구조)

from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine.url import make_url
from dotenv import load_dotenv

# =========================
# 0) .env 강제 로드
#    - 프로젝트 루트(…/Nozify) 혹은 backend/.env 를 탐색
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../Nozify
CANDIDATE_ENVS = [
    os.path.join(BASE_DIR, ".env"),
    os.path.join(BASE_DIR, "backend", ".env"),
]
ENV_PATH_USED = None
for p in CANDIDATE_ENVS:
    if os.path.exists(p):
        load_dotenv(p)  # override=False (기본): 이미 설정된 환경변수는 덮어쓰지 않음
        ENV_PATH_USED = p
        break
print("ENV_PATH_USED:", ENV_PATH_USED)

# =========================
# 1) 프로젝트 경로 추가 (.../Nozify/backend)
# =========================
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

# =========================
# 2) 앱 설정/모델 import
# =========================
from app.core.config import settings
from app.models.base import Base
from app import models  # noqa: F401  # autogenerate 위해 모델 import

# =========================
# 3) Alembic 기본 설정
# =========================
config = context.config

# 3-1) 연결 URL 결정 (우선순위: ENV -> settings.DATABASE_URL -> settings 조립)
env_url = os.getenv("DATABASE_URL")
settings_url = getattr(settings, "DATABASE_URL", None)

if env_url:
    database_url = env_url
    url_source = "ENV:DATABASE_URL"
elif settings_url:
    database_url = settings_url
    url_source = "settings.DATABASE_URL"
else:
    db_user = settings.DB_USER
    db_pass = settings.DB_PASSWORD
    db_host = settings.DB_HOST
    db_port = settings.DB_PORT
    db_name = settings.DB_NAME
    db_driver = getattr(settings, "DB_DRIVER", "pymysql").strip().lower()
    if db_driver not in ("pymysql", "mysqldb"):
        db_driver = "pymysql"
    database_url = f"mysql+{db_driver}://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    url_source = "assembled-from-settings"

# 3-2) ini보다 파이썬에서 DSN 강제 주입
config.set_main_option("sqlalchemy.url", database_url)

# 3-3) 최종 URL 요약 로깅 (비번 노출 안 함)
try:
    url_obj = make_url(database_url)
    print("ALEMBIC_URL_SOURCE:", url_source)
    print(
        "ALEMBIC_URL_SUMMARY ->",
        f"dialect+driver={url_obj.drivername}, "
        f"user={url_obj.username}, host={url_obj.host}, port={url_obj.port}, db={url_obj.database}",
    )
except Exception as e:
    print("ALEMBIC_URL 파싱 실패:", e)

# 3-4) 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3-5) autogenerate 메타데이터
target_metadata = Base.metadata


# =========================
# 4) Offline / Online
# =========================
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        pool_pre_ping=True,
    )

    with connectable.connect() as connection:
        # 연결 확인(문제 원인 찍기)
        try:
            who, db = connection.exec_driver_sql(
                "SELECT CURRENT_USER(), DATABASE();"
            ).fetchone()
            print("CONNECTED AS:", who, "DB:", db)
        except Exception as e:
            print("사전 연결 확인 쿼리 실패:", e)

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
