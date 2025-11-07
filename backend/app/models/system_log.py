from __future__ import annotations
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import JSON
from .base import Base, TimestampMixin

class SystemLog(Base, TimestampMixin):
    __tablename__ = "system_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # api_error, sync_error, warning, info, critical 등
    log_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info")

    message: Mapped[str | None] = mapped_column(Text)
    stack_trace: Mapped[str | None] = mapped_column(Text)

    # 파이썬 속성명은 meta, 실제 DB 컬럼명은 'metadata'로 유지
    meta: Mapped[dict | None] = mapped_column("metadata", JSON)
