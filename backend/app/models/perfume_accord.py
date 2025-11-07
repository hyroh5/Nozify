# backend/app/models/perfume_accord.py
from __future__ import annotations
from sqlalchemy import Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class PerfumeAccord(Base):
    __tablename__ = "perfume_accord"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    perfume_id: Mapped[int] = mapped_column(ForeignKey("perfume.id", ondelete="CASCADE"))
    accord_id: Mapped[int] = mapped_column(ForeignKey("accord.id", ondelete="CASCADE"))

    perfume = relationship("Perfume", backref="accord_links")
    accord = relationship("Accord", back_populates="perfumes")

    __table_args__ = (
        UniqueConstraint("perfume_id", "accord_id", name="uq_perfume_accord"),
    )
