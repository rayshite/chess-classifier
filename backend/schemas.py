"""
Pydantic-схемы для валидации данных API.
"""

from datetime import datetime

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr

from models import UserRole


class UserRead(schemas.BaseUser[int]):
    """Схема для чтения пользователя."""
    name: str
    role: UserRole
    created_at: datetime


class UserCreate(schemas.BaseUserCreate):
    """Схема для создания пользователя."""
    name: str
    role: UserRole = UserRole.STUDENT


class UserUpdate(schemas.BaseUserUpdate):
    """Схема для обновления пользователя."""
    name: str | None = None
    role: UserRole | None = None


class UserUpdateByAdmin(BaseModel):
    """Схема обновления пользователя администратором."""
    name: str | None = None
    email: EmailStr | None = None
    role: str | None = None
    is_active: bool | None = None


class UserCreateByAdmin(BaseModel):
    """Схема создания пользователя администратором."""
    name: str
    email: EmailStr
    role: str = "student"


class UserUpdateSelf(BaseModel):
    """Схема обновления своего профиля."""
    email: EmailStr | None = None
    password: str | None = None


class GameCreate(BaseModel):
    """Схема создания партии."""
    title: str
    player1_id: int
    player2_id: int
