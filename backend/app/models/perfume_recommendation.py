# backend/app/models/perfume_recommendation.py
from __future__ import annotations
from decimal import Decimal
from sqlalchemy import Integer, String, Text, Boolean, ForeignKey, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

class PerfumeRecommendation(Base, TimestampMixin):
    __tablename__ = "perfume_recommendation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False)
    perfume_id: Mapped[int] = mapped_column(ForeignKey("perfume.id", ondelete="CASCADE"), index=True, nullable=False)

    recommendation_type: Mapped[str] = mapped_column(String(50), nullable=False)  # pbti/similar/seasonal/trending
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    reason: Mapped[str | None] = mapped_column(Text)

    was_viewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    was_clicked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    was_added_to_wishlist: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", backref="recommendations")
    perfume = relationship("Perfume", backref="recommended_to")

    __table_args__ = (
        Index("ix_reco_user_type_score", "user_id", "recommendation_type", "score"),
        Index("ix_reco_perfume", "perfume_id"),
    )
