from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimeStampMixin

class Note(Base, TimeStampMixin):
    __tablename__ = "note"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
