# backend/app/models/pbti_result.py
from __future__ import annotations

from sqlalchemy import Integer, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.mysql import JSON, BINARY

from .base import Base, TimestampMixin

class PBTIResult(Base, TimestampMixin):
    __tablename__ = "pbti_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[bytes] = mapped_column(
        BINARY(16),
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # 0~100 점수
    temperature_score: Mapped[int] = mapped_column(Integer, nullable=False)
    texture_score: Mapped[int] = mapped_column(Integer, nullable=False)
    mood_score: Mapped[int] = mapped_column(Integer, nullable=False)
    nature_score: Mapped[int] = mapped_column(Integer, nullable=False)

    final_type: Mapped[str] = mapped_column(String(4), nullable=False)
    type_name: Mapped[str] = mapped_column(String(50), nullable=False)

    # [{"question_id": 1, "choice": 5, "axis": 1, "direction": 1, "score": 5}, ...]
    answers: Mapped[list[dict] | None] = mapped_column(JSON)

    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", backref="pbti_results")

    __table_args__ = (
        Index("ix_pbti_user_active", "user_id", "is_active"),
    )
