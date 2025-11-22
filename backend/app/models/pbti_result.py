from __future__ import annotations

from sqlalchemy import Integer, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.mysql import JSON, BINARY

from .base import Base, TimestampMixin


class PBTIResult(Base, TimestampMixin):
    __tablename__ = "pbti_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # user 테이블이 BINARY(16) PK라서 여기서도 동일하게 맞춤
    user_id: Mapped[bytes] = mapped_column(
        BINARY(16),
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # 각 축 점수 0~100
    temperature_score: Mapped[int | None] = mapped_column(Integer)
    texture_score: Mapped[int | None] = mapped_column(Integer)
    mood_score: Mapped[int | None] = mapped_column(Integer)
    nature_score: Mapped[int | None] = mapped_column(Integer)

    # 최종 타입 코드 예 FLSN
    final_type: Mapped[str | None] = mapped_column(String(4))

    # 타입 별 별칭 예 반짝이는 수영 요정
    type_name: Mapped[str | None] = mapped_column(String(50))

    # 원본 답안 저장
    # 예 [{"question_id": 1, "score": 5}, ...]
    answers: Mapped[dict | None] = mapped_column(JSON)

    # 유저가 현재 선택한 결과인지
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", backref="pbti_results")

    __table_args__ = (
        Index("ix_pbti_user_active", "user_id", "is_active"),
    )
