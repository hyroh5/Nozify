# backend/app/api/deps.py
from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_access_token
from app.models.user import User


# 💡 [수정] 함수의 반환 타입을 bytes -> User로 변경해야 합니다.
# 함수 이름은 그대로 두어 auth.py와의 호환성을 유지합니다.
def get_current_user_id(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User: # 👈 반환 타입을 User 모델로 지정
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")

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
        # 이전에 uuid_bytes_to_hex로 인코딩되었으므로, 디코딩 오류는 포맷 오류로 간주합니다.
        raise HTTPException(status_code=401, detail="Invalid user id format")

    # 🚨 [핵심 수정] DB에서 User 객체를 조회합니다.
    user = db.query(User).filter(User.id == user_id_bytes).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # 💡 [수정] user_id_bytes 대신, 조회한 user 객체를 반환합니다.
    return user