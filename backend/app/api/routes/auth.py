# backend/app/api/routes/auth.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserBase
from app.core.security import (
    create_access_token, create_refresh_token,
    hash_password, verify_password
)
from app.models.base import uuid_bytes_to_hex  # BINARY(16) -> hex 문자열

router = APIRouter(prefix="/auth", tags=["Auth"])

# 회원가입
@router.post("/signup")
def signup(data: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == data.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")

    new_user = User(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),  # 모델 컬럼명 확인!
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    uid_hex = uuid_bytes_to_hex(new_user.id)
    access_token = create_access_token({"sub": uid_hex})
    refresh_token = create_refresh_token({"sub": uid_hex})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": UserBase(id=uid_hex, name=new_user.name, email=new_user.email).model_dump(),
    }

# 로그인
@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")

    if not verify_password(data.password, user.hashed_password):  # 모델 컬럼명 확인!
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")

    uid_hex = uuid_bytes_to_hex(user.id)
    access_token = create_access_token({"sub": uid_hex})
    refresh_token = create_refresh_token({"sub": uid_hex})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": UserBase(id=uid_hex, name=user.name, email=user.email).model_dump(),
    }
