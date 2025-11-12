# backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr, ConfigDict

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
