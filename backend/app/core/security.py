# backend/app/core/security.py
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import jwt  # PyJWT
from passlib.context import CryptContext

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET", "dev-refresh-secret")
ACCESS_EXPIRE_MIN = int(os.getenv("ACCESS_EXPIRE_MIN", "60"))
REFRESH_EXPIRE_DAYS = int(os.getenv("REFRESH_EXPIRE_DAYS", "14"))

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def _encode(payload: Dict[str, Any], secret: str, minutes: int | None = None, days: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    exp = now + (timedelta(minutes=minutes) if minutes is not None else timedelta(days=days or 14))
    to_encode = payload.copy()
    to_encode.update({"iat": int(now.timestamp()), "exp": int(exp.timestamp())})
    return jwt.encode(to_encode, secret, algorithm="HS256")

def create_access_token(payload: Dict[str, Any]) -> str:
    return _encode(payload, JWT_SECRET, minutes=ACCESS_EXPIRE_MIN)

def create_refresh_token(payload: Dict[str, Any]) -> str:
    return _encode(payload, JWT_REFRESH_SECRET, days=REFRESH_EXPIRE_DAYS)

def decode_access_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

def decode_refresh_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, JWT_REFRESH_SECRET, algorithms=["HS256"])
