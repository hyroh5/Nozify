import sys, os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 경로 설정: NOZIFY/backend를 sys.path에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.config import settings
from app.models.base import Base
from app import models  # 모든 모델 import해서 Alembic이 인식하게
