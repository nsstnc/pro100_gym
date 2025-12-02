from pydantic import BaseModel, EmailStr
from typing import Any, Optional, Dict


class StandardResponse(BaseModel):
    status_code: int
    error: Optional[Any] = None
    data: Optional[Any] = None
    path: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


# --- JWT Схемы ---
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# --- Схемы пользователя ---
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int

    class Config:
        from_attributes = True
