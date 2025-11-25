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
    """
    로그인 필수 계에서 사용하는 계.
    Authorization 헤더가 없거나, 토큰이 잘못되면 401 에러를 내고 종료.
    """
    if not authorization:
        # 비로그인 상태 → 바로 401
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty access token")

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


def get_current_user_optional(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User | None:
    """
    로그인 여부 선택 계에서 사용하는 계.
    - Authorization 헤더가 없으면: None 반환 → 비로그인 상태로 취급
    - 헤더는 있는데 토큰이 잘못되면: 401/403 은 None 으로 처리
    """
    # 완전 비로그인 요청
    if not authorization:
        return None

    try:
        # 위에서 정의한 엄격 버전을 재사용
        return get_current_user_id(authorization=authorization, db=db)
    except HTTPException as e:
        # 인증 실패 계는 "그냥 비로그인 상태"로 간주
        if e.status_code in (401, 403):
            return None
        # 다른 에러는 그대로 올림
        raise
