# backend/app/models/seasonal_recommendation.py
from __future__ import annotations
from sqlalchemy import Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import JSON
from .base import Base, TimestampMixin

class SeasonalRecommendation(Base, TimestampMixin):
    __tablename__ = "seasonal_recommendation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    season: Mapped[str] = mapped_column(String(20), nullable=False)  # spring/summer/fall/winter
    category: Mapped[str | None] = mapped_column(String(50))
    title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)

    perfume_ids: Mapped[list | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int | None] = mapped_column(Integer)
