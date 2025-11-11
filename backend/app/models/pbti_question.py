# backend/app/models/pbti_question.py
from __future__ import annotations
from sqlalchemy import Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin

class PBTIQuestion(Base, TimestampMixin):
    __tablename__ = "pbti_question"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)  # 1~4
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # 필요 시: choice_scale 등 추가 가능
