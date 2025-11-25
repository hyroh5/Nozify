# backend/app/api/deps.py
from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_access_token
from app.models.user import User


def _decode_user_from_token(token: str, db: Session) -> User:
    """
    내부 헬퍼: access token -> User
    (get_current_user_id, get_current_user_optional 둘 다에서 공통 사용)
    """
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


def get_current_user_id(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    """
    로그인 필수 엔드포인트용.
    - Authorization 헤더가 없거나
    - 토큰이 잘못되면
      → 401 에러를 바로 발생시킴.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty token")

    return _decode_user_from_token(token, db)


def get_current_user_optional(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User | None:
    """
    비로그인 허용 엔드포인트용.
    - Authorization 헤더가 없거나
    - 토큰이 이상하면
      → 에러 대신 그냥 None 리턴.
    """
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None

    try:
        return _decode_user_from_token(token, db)
    except HTTPException:
        # 토큰이 깨졌거나 유저가 없으면 "로그인 안 한 것"으로 처리
        return None
