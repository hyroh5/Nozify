# backend/app/models/refresh_token.py
from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.dialects.mysql import BINARY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

class RefreshToken(Base, TimestampMixin):
    __tablename__ = "refresh_token"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[bytes] = mapped_column(
        BINARY(16), 
        ForeignKey("user.id", ondelete="CASCADE"), 
        index=True
    )

    token: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_user", "user_id"),
        Index("ix_refresh_expires", "expires_at"),
    )
