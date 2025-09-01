# alembic/env.py  — Nozify용(MySQL, backend/app 구조)
from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ============================================
# 1) 프로젝트 경로 추가 (…/NOZIFY/backend 를 sys.path에)
#    env.py 위치: NOZIFY/alembic/env.py
# ============================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # NOZIFY
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

# ============================================
# 2) 앱 설정/모델 불러오기
#    - Settings(.env 로딩)
#    - Base.metadata: autogenerate 대상
#    - 모든 모델 import: Alembic이 테이블 변화를 감지하도록
# ============================================
from app.core.config import settings
from app.models.base import Base

# 모델 모듈들을 여기서 import 해야 autogenerate가 감지함
# 예: from app.models import brand, note, perfume, perfume_note, user, diary ...
# 일단 패키지 전체 import(각 __init__에서 내부 모듈 import하도록 구성하는 게 깔끔)
from app import models  # noqa: F401  (모델 하위 모듈에서 Base에 테이블 등록된다는 가정)

# ============================================
# 3) Alembic 기본 설정
# ============================================
config = context.config

# .ini가 아닌 파이썬에서 DSN을 주입 (MySQL)
config.set_main_option(
    "sqlalchemy.url",
    (
        f"mysql+mysqldb://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        f"?charset=utf8mb4"
    ),
)

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# autogenerate가 참조할 메타데이터
target_metadata = Base.metadata


# ============================================
# 4) Offline / Online 런너
# ============================================
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # 컬럼 타입 변경 감지
        compare_server_default=True,  # 서버 default 변경 감지
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
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
