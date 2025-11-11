# backend/app/models/calendar.py
from __future__ import annotations
from datetime import date
from sqlalchemy import Integer, String, Date, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

class PerfumeCalendar(Base, TimestampMixin):
    __tablename__ = "perfume_calendar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    perfume_id: Mapped[int] = mapped_column(ForeignKey("perfume.id", ondelete="CASCADE"), index=True)

    wear_date: Mapped[date] = mapped_column(Date, nullable=False)
    situation: Mapped[str | None] = mapped_column(String(50))
    weather:   Mapped[str | None] = mapped_column(String(50))
    mood:      Mapped[str | None] = mapped_column(String(50))
    memo:      Mapped[str | None] = mapped_column(String(500))

    user = relationship("User", backref="perfume_days")
    perfume = relationship("Perfume", backref="calendar_entries")

    __table_args__ = (
        UniqueConstraint("user_id", "wear_date", "perfume_id", name="uq_calendar_user_date_perfume"),
        Index("ix_calendar_user_date", "user_id", "wear_date"),
        Index("ix_calendar_perfume", "perfume_id"),
    )
