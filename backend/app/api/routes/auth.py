from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.user import ( UserCreate, UserLogin, UserResponse, UserBase, RefreshRequest, TokenResponse,   ChangePasswordRequest, UpdateProfileRequest )
from app.core.security import (
    create_access_token, create_refresh_token,
    hash_password, verify_password
)
from datetime import timedelta
from passlib.hash import bcrypt
from app.models.base import uuid_bytes_to_hex
from app.api.deps import get_current_user_id

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
    rt = RefreshToken(user_id=new_user.id, token=refresh_token, revoked=False)
    db.add(rt); db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": uid_hex,
            "name": new_user.name,
            "email": new_user.email,
        },
    }


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
    rt = RefreshToken(user_id=new_user.id, token=refresh_token, revoked=False)
    db.add(rt); db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": uid_hex,
            "name": user.name,
            "email": user.email,
        },
    }

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    # 1) 토큰 디코드
    try:
        decoded = decode_token(payload.refresh_token, refresh=True)
    except Exception:
        raise HTTPException(status_code=401, detail="유효하지 않은 리프레시 토큰입니다.")

    user_id = decoded.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="유효하지 않은 리프레시 토큰입니다.")

    # 2) (선택) DB에 저장된 리프레시 토큰이 있는지 확인
    rt = db.query(RefreshToken).filter(
        RefreshToken.user_id == bytes.fromhex(user_id),
        RefreshToken.token == payload.refresh_token,
        RefreshToken.revoked == False
    ).first()
    if not rt:
        # 저장형을 쓰지 않는다면 이 체크는 제거해도 됨
        raise HTTPException(status_code=401, detail="등록되지 않았거나 취소된 리프레시 토큰입니다.")

    # 3) 새 access token 발급
    new_access = create_access_token({"sub": user_id}, expires_delta=timedelta(hours=1))
    return TokenResponse(access_token=new_access)


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
):
    # 기존 비밀번호 검증
    if not verify_password(body.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 일치하지 않습니다.")

    # 새 비밀번호 저장
    current_user.password_hash = hash_password(body.new_password)
    db.add(current_user)

    # 보안을 위해 기존 refresh 토큰들 무효화
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id
    ).update({"revoked": True})
    db.commit()
    return {"message": "Password updated successfully"}


@router.patch("/update-profile", response_model=UserBase)
def update_profile(
    body: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
):
    # 이메일 변경 시 중복 체크
    if body.email and body.email != current_user.email:
        exists = db.query(User).filter(User.email == body.email).first()
        if exists:
            raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")
        current_user.email = body.email

    if body.name:
        current_user.name = body.name

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return UserBase.model_validate({
        "id": uuid_bytes_to_hex(current_user.id),
        "name": current_user.name,
        "email": current_user.email,
    })