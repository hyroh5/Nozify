# backend/app/models/base.py
from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import func

class Base(DeclarativeBase):
    """모든 ORM 모델의 공통 Base"""
    pass

class TimestampMixin:
    """created_at / updated_at 공통 컬럼 믹스인"""
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# UUID BINARY(16) <-> hex string
def uuid_bytes_to_hex(b: bytes | None) -> str | None:
    if not b:
        return None
    import uuid
    return uuid.UUID(bytes=b).hex

def uuid_hex_to_bytes(h: str | None) -> bytes | None:
    if not h:
        return None
    import uuid
    return uuid.UUID(hex=h).bytes
