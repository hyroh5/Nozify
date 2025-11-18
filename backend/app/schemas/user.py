# backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional

# 요청 스키마
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# 응답용 유저 베이스
class UserBase(BaseModel):
    id: str          # BINARY(16) → hex 문자열로 변환해서 담을 예정
    name: str
    email: EmailStr

    # Pydantic v2
    model_config = ConfigDict(from_attributes=True)

# 토큰 페어
class TokenPair(BaseModel):
    access_token: str
    refresh_token: str

# 로그인/회원가입 응답 통합
class UserResponse(TokenPair):
    user: UserBase

class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None  # refresh는 /login, /signup 때만 함께 내려감

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=4)
    new_password: str = Field(min_length=8)

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None