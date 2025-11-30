"""
Роутер для API пользователей.
"""

import secrets
import string

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from auth import current_active_user
from database import get_async_session
from models import User, UserRole
from services import get_users_list, get_users_count, get_user_by_id

router = APIRouter(prefix="/api/users", tags=["users"])


def generate_temp_password(length: int = 10) -> str:
    """Генерирует временный пароль."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class UserUpdateByAdmin(BaseModel):
    """Схема обновления пользователя администратором."""
    name: str | None = None
    email: EmailStr | None = None
    role: UserRole | None = None
    is_active: bool | None = None


@router.get("")
async def get_users(
    page: int = 1,
    limit: int = 10,
    role: str | None = None,
    session: AsyncSession = Depends(get_async_session)
):
    """Получить список пользователей с пагинацией и фильтрацией"""
    page = max(1, page)
    limit = min(max(1, limit), 100)

    role_filter = None
    if role and role != 'all':
        try:
            role_filter = UserRole(role)
        except ValueError:
            pass

    offset = (page - 1) * limit

    users = await get_users_list(session, role=role_filter, limit=limit, offset=offset)
    total_count = await get_users_count(session, role=role_filter)
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

    users_data = [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "isActive": user.is_active,
            "createdAt": user.created_at.isoformat()
        }
        for user in users
    ]

    return {
        "users": users_data,
        "pagination": {
            "currentPage": page,
            "totalPages": total_pages,
            "totalCount": total_count,
            "limit": limit
        }
    }


@router.patch("/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdateByAdmin,
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(current_active_user)
):
    """Обновить пользователя (только для админов)."""
    if admin.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Только администратор может редактировать пользователей")

    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Обновляем поля
    if data.name is not None:
        user.name = data.name
    if data.email is not None:
        user.email = data.email
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active

    await session.commit()
    await session.refresh(user)

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
        "isActive": user.is_active
    }


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(current_active_user)
):
    """Сбросить пароль пользователя (только для админов)."""
    if admin.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Только администратор может сбрасывать пароли")

    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Генерируем временный пароль
    temp_password = generate_temp_password()

    # Хешируем пароль
    from pwdlib import PasswordHash
    ph = PasswordHash.recommended()
    user.hashed_password = ph.hash(temp_password)

    await session.commit()

    return {
        "message": "Пароль сброшен",
        "temporaryPassword": temp_password
    }
