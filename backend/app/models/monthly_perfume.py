# backend/app/models/monthly_perfume.py
from __future__ import annotations
from sqlalchemy import Integer, String, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

class MonthlyPerfume(Base, TimestampMixin):
    __tablename__ = "monthly_perfume"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    perfume_id: Mapped[int] = mapped_column(ForeignKey("perfume.id", ondelete="CASCADE"), nullable=False)

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)

    title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)

    display_order: Mapped[int | None] = mapped_column(Integer)

    perfume = relationship("Perfume", backref="monthly_features")

    __table_args__ = (
        UniqueConstraint("perfume_id", "year", "month", name="uq_monthly_perfume_year_month"),
        Index("ix_monthly_perfume_year_month", "year", "month"),
    )
