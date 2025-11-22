# backend/app/api/deps.py
from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_access_token
from app.models.user import User


def get_current_user_id(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None

    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid access token")

    user_id_hex = payload.get("sub")
    if not user_id_hex:
        raise HTTPException(status_code=401, detail="Invalid access token no sub")

    try:
        user_id_bytes = bytes.fromhex(user_id_hex)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid user id format")

    user = db.query(User).filter(User.id == user_id_bytes).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user