"""
Pydantic схемы для fastapi-users.
"""

from datetime import datetime

from fastapi_users import schemas
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
