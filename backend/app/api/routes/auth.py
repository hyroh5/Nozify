# backend/app/api/routes/auth.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.user import ( UserCreate, UserLogin, UserResponse, UserBase, RefreshRequest, TokenResponse, 
    ChangePasswordRequest, UpdateProfileRequest )
from app.core.security import (
    create_access_token, create_refresh_token,
    hash_password, verify_password, decode_token # 💡 [수정] decode_token 임포트
)
from datetime import timedelta

from app.models.base import uuid_bytes_to_hex
from app.api.deps import get_current_user_id
import jwt # jwt 임포트 (ExpiredSignatureError 처리용)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserResponse)
def signup(data: UserCreate, db: Session = Depends(get_db)):
    # 이메일 중복 체크
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")

    # 비밀번호 해시 저장
    hashed_pw = hash_password(data.password)
    new_user = User(
        name=data.name,
        email=data.email,
        password_hash=hashed_pw,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    uid_hex = uuid_bytes_to_hex(new_user.id)

    access_token = create_access_token({"sub": uid_hex})
    refresh_token = create_refresh_token({"sub": uid_hex})

    # 🔹 혹시라도 기존 토큰이 남아있으면 전부 revoke
    db.query(RefreshToken).filter(
        RefreshToken.user_id == new_user.id,
        RefreshToken.revoked == False
    ).update({"revoked": True})

    rt = RefreshToken(
        user_id=new_user.id,
        token=refresh_token,
        revoked=False,
    )
    db.add(rt)
    db.commit()

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
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")

    uid_hex = uuid_bytes_to_hex(user.id)

    access_token = create_access_token({"sub": uid_hex})
    refresh_token = create_refresh_token({"sub": uid_hex})

    # 🔹 기존 유효한 refresh 토큰들 전부 revoke
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked == False
    ).update({"revoked": True})

    rt = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        revoked=False,
    )
    db.add(rt)
    db.commit()

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
    # 1) 토큰 디코드 및 만료 검증
    try:
        # 💡 [수정] 오타 수정: decode__refresh_token -> decode_token
        decoded = decode_token(payload.refresh_token, refresh=True) 
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="리프레시 토큰이 만료되었습니다. 다시 로그인해주세요.")
    except Exception:
        raise HTTPException(status_code=401, detail="유효하지 않은 리프레시 토큰입니다.")

    user_id = decoded.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="유효하지 않은 리프레시 토큰입니다.")

    # 2) DB에 저장된 리프레시 토큰이 있는지 확인 (user_id는 hex string을 bytes로 변환)
    rt = db.query(RefreshToken).filter(
        RefreshToken.user_id == bytes.fromhex(user_id),
        RefreshToken.token == payload.refresh_token,
        RefreshToken.revoked == False
    ).first()
    if not rt:
        raise HTTPException(status_code=401, detail="등록되지 않았거나 취소된 리프레시 토큰입니다.")

    # 3) 새 access token 발급
    new_access = create_access_token({"sub": user_id}) # expires_delta 삭제 (security.py에서 처리됨)
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

@router.get("/me", response_model=UserBase)
def get_current_user_profile(
    current_user: User = Depends(get_current_user_id), # User 객체를 주입받음
):
    """현재 로그인된 사용자의 기본 정보를 조회합니다."""
    # current_user는 User 모델 객체이므로 바로 접근 가능
    
    # UserBase 스키마에 맞게 데이터를 포맷하여 반환
    return UserBase.model_validate({
        "id": uuid_bytes_to_hex(current_user.id),
        "name": current_user.name,
        "email": current_user.email,
    })

@router.post("/logout")
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    """리프레시 토큰을 무효화하여 로그아웃합니다."""
    
    # 1. 토큰 디코드 시도 (유효성 확인 및 user_id 추출)
    try:
        # decode_token 사용, refresh=True 전달
        decoded = decode_token(payload.refresh_token, refresh=True) 
    except Exception:
        # 서명 오류, 만료 오류 등은 모두 유효하지 않은 토큰으로 처리
        raise HTTPException(status_code=401, detail="유효하지 않은 리프레시 토큰입니다.")

    user_id_hex = decoded.get("sub")
    if not user_id_hex:
        raise HTTPException(status_code=401, detail="토큰에 사용자 정보가 없습니다.")

    # 2. DB에서 해당 토큰을 찾아 무효화 (revoked=True)
    try:
        user_id_bytes = bytes.fromhex(user_id_hex)
    except Exception:
        raise HTTPException(status_code=401, detail="유효하지 않은 사용자 ID 포맷입니다.")
        
    updated = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id_bytes,
        RefreshToken.token == payload.refresh_token,
        RefreshToken.revoked == False
    ).update({"revoked": True})
    
    if updated == 0:
        # 토큰이 이미 무효화되었거나 존재하지 않는 경우
        raise HTTPException(status_code=400, detail="이미 무효화되었거나 유효하지 않은 토큰입니다.")
        
    db.commit()
    
    return {"message": "Logged out successfully."}


@router.delete("/me", status_code=204)
def delete_user_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id), # 삭제할 User 객체
):
    """현재 로그인된 사용자의 계정을 탈퇴(삭제)합니다."""
    
    # 1. 사용자 삭제
    # SQLAlchemy의 세션을 통해 current_user 객체를 삭제합니다.
    db.delete(current_user)
    
    # 2. CASCADE 적용 및 커밋
    # User 모델의 id에 Foreign Key로 연결된 다른 테이블(예: refresh_token)의 
    # 데이터는 ON DELETE CASCADE 설정에 의해 자동으로 삭제됩니다.
    db.commit()
    
    return