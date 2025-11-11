# backend/app/models/image_recognition_log.py
from __future__ import annotations
from sqlalchemy import Integer, String, Text, ForeignKey, Numeric, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.mysql import JSON
from .base import Base, TimestampMixin

class ImageRecognitionLog(Base, TimestampMixin):
    __tablename__ = "image_recognition_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"))
    recognized_perfume_id: Mapped[int | None] = mapped_column(ForeignKey("perfume.id", ondelete="SET NULL"))
    actual_perfume_id: Mapped[int | None] = mapped_column(ForeignKey("perfume.id", ondelete="SET NULL"))

    image_url: Mapped[str | None] = mapped_column(Text)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(5, 4))
    candidate_perfumes: Mapped[list | None] = mapped_column(JSON)  # [{perfume_id, score}, ...]

    model_version: Mapped[str | None] = mapped_column(String(50))
    processing_time_ms: Mapped[int | None] = mapped_column(Integer)

    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", backref="recognition_logs")
    recognized_perfume = relationship("Perfume", foreign_keys=[recognized_perfume_id])
    actual_perfume = relationship("Perfume", foreign_keys=[actual_perfume_id])

    __table_args__ = (
        Index("ix_recog_user", "user_id"),
        Index("ix_recog_model", "model_version"),
    )
