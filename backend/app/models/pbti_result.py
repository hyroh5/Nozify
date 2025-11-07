# backend/app/models/pbti_result.py
from __future__ import annotations
from sqlalchemy import Integer, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.mysql import JSON
from .base import Base, TimestampMixin

class PBTIResult(Base, TimestampMixin):
    __tablename__ = "pbti_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False)

    # 0~100 점수(정수형)
    dimension_1_score: Mapped[int | None] = mapped_column(Integer)
    dimension_2_score: Mapped[int | None] = mapped_column(Integer)
    dimension_3_score: Mapped[int | None] = mapped_column(Integer)
    dimension_4_score: Mapped[int | None] = mapped_column(Integer)

    final_type: Mapped[str | None] = mapped_column(String(4))     # 예: FLSN
    type_name:  Mapped[str | None] = mapped_column(String(50))    # 예: "반짝이는 수영 요정"

    answers: Mapped[dict | None] = mapped_column(JSON)            # [{question_id, score}, ...]

    # 사용자가 “현재 선택한” 결과를 표시(여러 결과 중 UI에서 토글)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", backref="pbti_results")

    __table_args__ = (
        Index("ix_pbti_user_active", "user_id", "is_active"),
    )
