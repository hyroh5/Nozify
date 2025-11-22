from __future__ import annotations

from sqlalchemy import Integer, String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class PBTIRecommendation(Base, TimestampMixin):
    __tablename__ = "pbti_recommendation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # PBTI 타입 코드 (예: "fresh-light", "warm-heavy", "FLSN"...)
    type_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # 추천 향수 ID
    perfume_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("perfume.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 매칭 점수 (0~1 또는 가중치 기반)
    match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # 관계 연결
    perfume = relationship("Perfume", backref="pbti_recommendations")
