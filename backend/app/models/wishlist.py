# backend/app/models/wishlist.py
from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

class Wishlist(Base, TimestampMixin):
    __tablename__ = "wishlist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    perfume_id: Mapped[int] = mapped_column(ForeignKey("perfume.id", ondelete="CASCADE"), index=True)

    # 관계
    user = relationship("User", backref="wishlists")
    perfume = relationship("Perfume", backref="wished_by")

    __table_args__ = (
        UniqueConstraint("user_id", "perfume_id", name="uq_wishlist_user_perfume"),
        Index("ix_wishlist_user", "user_id"),
        Index("ix_wishlist_perfume", "perfume_id"),
    )
