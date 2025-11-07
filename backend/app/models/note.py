# backend/app/models/note.py
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Note(Base):
    __tablename__ = "note"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    family = Column(String(50), nullable=True)       # 플로럴, 시트러스 등
    alias = Column(String(100), nullable=True)       # 다른 표기 보조

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    perfumes = relationship("PerfumeNote", back_populates="note", cascade="all, delete-orphan")
