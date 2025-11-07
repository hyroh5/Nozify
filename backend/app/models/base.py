# backend/app/models/base.py
from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import func

class Base(DeclarativeBase):
    """모든 ORM 모델의 공통 Base"""
    pass

class TimestampMixin:
    """created_at / updated_at 공통 컬럼 믹스인"""
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

# 과거 오타 호환용. 나중에 지워도 됨.
TimeStampMixin = TimestampMixin
