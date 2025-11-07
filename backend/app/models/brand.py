from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models.base import Base
from sqlalchemy.dialects.mysql import BINARY
import uuid

class Brand(Base):
    __tablename__ = "brand"

    id = Column(BINARY(16), primary_key=True, default=lambda: uuid.uuid4().bytes, index=True) 
    
    name = Column(String(255), unique=True, index=True)
    logo_url = Column(String(512), nullable=True)

    perfumes = relationship("Perfume", back_populates="brand")