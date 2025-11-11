# backend/app/models/base.py

from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import func
import uuid

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

# 이미 있다면 그대로 두세요
def uuid_bytes_to_hex(b: bytes | None) -> str | None:
    if not b:
        return None
    return uuid.UUID(bytes=b).hex

def uuid_hex_to_bytes(h: str) -> bytes:
    # 기존 함수는 예외를 던지는 버전
    h = (h or "").replace("-", "").strip()
    return uuid.UUID(hex=h).bytes

def try_uuid_hex_to_bytes(h: str) -> bytes | None:
    if not h:
        return None
    h = h.replace("-", "").strip()
    if len(h) != 32:
        return None
    try:
        return uuid.UUID(hex=h).bytes
    except Exception:
        return None
