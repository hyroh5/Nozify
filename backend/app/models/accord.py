# backend/app/models/accord.py
from __future__ import annotations
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

class Accord(Base, TimestampMixin):
    __tablename__ = "accord"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name_korean: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    occurrence: Mapped[int | None] = mapped_column(Integer)

    perfumes = relationship("PerfumeAccord", back_populates="accord")
