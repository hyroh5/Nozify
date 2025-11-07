# backend/app/models/perfume_note.py
from sqlalchemy import Column, Integer, ForeignKey, Enum, Float, UniqueConstraint
from sqlalchemy.orm import relationship
import enum
from .base import Base, TimestampMixin
from sqlalchemy.dialects.mysql import BINARY

class NoteRole(str, enum.Enum):
    top = "top"
    middle = "middle"
    base = "base"

class PerfumeNote(Base):
    __tablename__ = "perfume_note"

    id = Column(Integer, primary_key=True, autoincrement=True)
    perfume_id = Column(BINARY(16), ForeignKey("perfume.id", ondelete="CASCADE"), nullable=False, index=True)
    note_id = Column(Integer, ForeignKey("note.id", ondelete="CASCADE"), nullable=False, index=True)

    role = Column(Enum(NoteRole), nullable=False)   # 탑 미들 베이스
    weight = Column(Float, nullable=True)           # 0.0~1.0 권장. 없으면 None

    __table_args__ = (
        UniqueConstraint("perfume_id", "note_id", "role", name="uq_perfume_note_role"),
    )

    perfume = relationship("Perfume", back_populates="notes")
    note = relationship("Note", back_populates="perfumes")
