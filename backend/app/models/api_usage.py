# backend/app/models/api_usage.py
from __future__ import annotations
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin

class APIUsage(Base, TimestampMixin):
    __tablename__ = "api_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)

    # 로그인 안 한 경우 None 허용. 필요한 경우 FK로 확장 가능
    user_id: Mapped[int | None] = mapped_column(nullable=True)

    response_time_ms: Mapped[int | None] = mapped_column(Integer)
    status_code: Mapped[int | None] = mapped_column(Integer)
