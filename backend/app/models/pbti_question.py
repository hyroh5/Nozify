# backend/app/models/pbti_question.py
from __future__ import annotations

from sqlalchemy import Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin


class PBTIQuestion(Base, TimestampMixin):
    __tablename__ = "pbti_question"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # temperature | texture | mood | nature
    axis: Mapped[str] = mapped_column(String(20), nullable=False)

    # +1 정방향, -1 역방향
    direction: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    text: Mapped[str] = mapped_column(Text, nullable=False)

    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
