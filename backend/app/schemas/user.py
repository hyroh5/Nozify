# backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserBase(BaseModel):
    id: str
    name: str
    email: EmailStr

    class Config:
        from_attributes = True  # Pydantic v2
