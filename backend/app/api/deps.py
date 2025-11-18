# backend/app/api/deps.py
from __future__ import annotations
from fastapi import Header, HTTPException
from typing import Optional

def get_current_user_id(
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")
) -> Optional[int]:
    """
    정수 기반 user.id 사용. 헤더가 없으면 None 반환(비개인화).
    정수 문자열만 허용.
    """
    if x_user_id is None:
        return None
    s = x_user_id.strip()
    if s.isdigit():
        return int(s)
    raise HTTPException(status_code=400, detail="invalid X-User-Id (integer)")
