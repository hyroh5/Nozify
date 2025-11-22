# backend/app/core/security.py
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import jwt
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
    
    # 💡 [개선] 만료 시간 설정 명확화
    if minutes is not None:
        expiry_delta = timedelta(minutes=minutes)
    elif days is not None:
        expiry_delta = timedelta(days=days)
    else:
        # 기본값 (접근 토큰 만료 시간 사용)
        expiry_delta = timedelta(minutes=ACCESS_EXPIRE_MIN) 
        
    exp = now + expiry_delta
    
    to_encode = payload.copy()
    to_encode.update({"iat": int(now.timestamp()), "exp": int(exp.timestamp())})
    return jwt.encode(to_encode, secret, algorithm="HS256")

def create_access_token(payload: Dict[str, Any]) -> str:
    return _encode(payload, JWT_SECRET, minutes=ACCESS_EXPIRE_MIN)

def create_refresh_token(payload: Dict[str, Any]) -> str:
    return _encode(payload, JWT_REFRESH_SECRET, days=REFRESH_EXPIRE_DAYS)

def decode_access_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])


# 🆕 [추가] 액세스 또는 리프레시 토큰을 디코드하는 통합 함수 (refresh 엔드포인트에서 필요)
def decode_token(token: str, refresh: bool = False) -> Dict[str, Any]:
    """
    토큰을 디코드합니다. refresh=True인 경우 리프레시 시크릿을 사용하고, 
    만료 검증을 비활성화합니다 (만료된 토큰을 디코드할 수 있어야 DB 검증으로 넘어감).
    """
    secret = JWT_REFRESH_SECRET if refresh else JWT_SECRET
    
    options = {}
    if refresh:
        # 리프레시 토큰의 만료 시간을 JWT 라이브러가 아닌 DB에서 확인하기 위해 EXP 검증 비활성화
        options["verify_exp"] = False 

    return jwt.decode(
        token, 
        secret, 
        algorithms=["HS256"], 
        options=options
    )