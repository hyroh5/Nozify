from sqlalchemy import Integer, String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimeStampMixin

class Perfume(Base, TimeStampMixin):
    __tablename__ = "perfume"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brand.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(255))
    price: Mapped[float | None] = mapped_column(Float)
    longevity: Mapped[int | None] = mapped_column(Integer)
    sillage: Mapped[int | None] = mapped_column(Integer)

    brand = relationship("Brand", back_populates="perfumes")
