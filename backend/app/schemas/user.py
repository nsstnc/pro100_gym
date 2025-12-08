from pydantic import BaseModel, EmailStr
from typing import Optional
from decimal import Decimal


class UserBase(BaseModel):
    username: str
    email: EmailStr
    telegram_id: Optional[int] = None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    weight: Optional[Decimal] = None
    height: Optional[int] = None
    age: Optional[int] = None
    fitness_goal: Optional[str] = None
    experience_level: Optional[str] = None
    workouts_per_week: Optional[int] = None
    session_duration: Optional[int] = None

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    weight: Optional[Decimal] = None
    height: Optional[int] = None
    age: Optional[int] = None
    fitness_goal: Optional[str] = None
    experience_level: Optional[str] = None
    workouts_per_week: Optional[int] = None
    session_duration: Optional[int] = None
