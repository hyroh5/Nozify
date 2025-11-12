from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.core.security import (
    create_access_token, create_refresh_token,
    hash_password, verify_password
)
from datetime import timedelta
from passlib.hash import bcrypt
from app.models.base import uuid_bytes_to_hex

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserResponse)
def signup(data: UserCreate, db: Session = Depends(get_db)):
    # 이메일 중복 체크
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")

    # 비밀번호 해시 저장 - 모델 컬럼명은 'password_hash' 기준
    hashed_pw = hash_password(data.password)
    new_user = User(
        name=data.name,
        email=data.email,
        password_hash=hashed_pw,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 핵심: BINARY(16) -> hex 문자열로 변환
    uid_hex = uuid_bytes_to_hex(new_user.id)

    # 토큰 payload의 sub도 문자열(hex)로
    access_token = create_access_token({"sub": uid_hex})
    refresh_token = create_refresh_token({"sub": uid_hex})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": uid_hex,
            "name": new_user.name,
            "email": new_user.email,
        },
    }

# 로그인
@router.post("/login", response_model=UserResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not bcrypt.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")

    # 핵심: BINARY(16) -> hex 문자열로 변환
    uid_hex = uuid_bytes_to_hex(user.id)

    # 토큰 payload의 sub도 문자열(hex)로
    access_token = create_access_token({"sub": uid_hex})
    refresh_token = create_refresh_token({"sub": uid_hex})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": uid_hex,
            "name": user.name,
            "email": user.email,
        },
    }