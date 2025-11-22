from __future__ import annotations

from sqlalchemy import Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class PBTIQuestion(Base, TimestampMixin):
    __tablename__ = "pbti_question"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 축 이름: temperature, texture, mood, nature
    axis: Mapped[str] = mapped_column(String(20), nullable=False)

    # 정방향이면 +1, 역문항이면 -1
    direction: Mapped[int] = mapped_column(Integer, nullable=False)

    # 질문 본문
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # 사용 여부
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
