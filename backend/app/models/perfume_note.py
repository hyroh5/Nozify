from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimeStampMixin

class PerfumeNote(Base, TimeStampMixin):
    __tablename__ = "perfume_note"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    perfume_id: Mapped[int] = mapped_column(ForeignKey("perfume.id"))
    note_id: Mapped[int] = mapped_column(ForeignKey("note.id"))
