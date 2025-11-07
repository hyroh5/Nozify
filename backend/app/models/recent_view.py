# backend/app/models/recent_view.py
from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class RecentView(Base):
    __tablename__ = "recent_view"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    perfume_id: Mapped[int] = mapped_column(ForeignKey("perfume.id", ondelete="CASCADE"), index=True)

    viewed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = relationship("User", backref="recent_views")
    perfume = relationship("Perfume", backref="viewed_by")

    __table_args__ = (
        # 같은 향수를 여러 번 봐도 한 줄만 유지하고 viewed_at만 갱신하는 전략
        UniqueConstraint("user_id", "perfume_id", name="uq_recent_user_perfume"),
        Index("ix_recent_user_viewed_at", "user_id", "viewed_at"),
    )
