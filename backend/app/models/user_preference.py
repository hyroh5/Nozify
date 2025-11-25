# backend/app/models/user_preference.py
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Integer, String, Numeric, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.mysql import JSON
from .base import Base, TimestampMixin


class UserPreference(Base, TimestampMixin):
    __tablename__ = "user_preference"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)

    preferred_accords: Mapped[dict | None] = mapped_column(JSON)
    preferred_brands:  Mapped[list | None] = mapped_column(JSON)
    price_range_min:   Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    price_range_max:   Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    preferred_seasons: Mapped[list | None] = mapped_column(JSON)
    preferred_occasions: Mapped[list | None] = mapped_column(JSON)

    last_calculated_at: Mapped[datetime | None] = mapped_column(DateTime)

    user = relationship("User", backref="preference")

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_preference_user"),
        Index("ix_user_pref_user", "user_id"),
    )
