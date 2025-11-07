# backend/app/models/purchase_history.py
from __future__ import annotations
from datetime import date
from sqlalchemy import Integer, Date, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

class PurchaseHistory(Base, TimestampMixin):
    __tablename__ = "purchase_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    perfume_id: Mapped[int] = mapped_column(ForeignKey("perfume.id", ondelete="CASCADE"), index=True)

    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    user = relationship("User", backref="purchases")
    perfume = relationship("Perfume", backref="purchased_in")

    __table_args__ = (
        Index("ix_purchase_user_date", "user_id", "purchase_date"),
        Index("ix_purchase_perfume", "perfume_id"),
    )
