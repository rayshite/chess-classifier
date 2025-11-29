"""
Роутер для API пользователей.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from models import UserRole
from services import (
    get_users_list,
    get_users_count,
    get_user_by_email,
    create_user,
)

router = APIRouter(prefix="/api/users", tags=["users"])


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


@router.post("")
async def create_new_user(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    """Создать нового пользователя"""
    data = await request.json()

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    role = data.get("role", "student")

    if not name:
        raise HTTPException(status_code=400, detail="Имя обязательно")
    if not email:
        raise HTTPException(status_code=400, detail="Email обязателен")
    if not password:
        raise HTTPException(status_code=400, detail="Пароль обязателен")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Пароль должен быть не менее 6 символов")

    existing_user = await get_user_by_email(session, email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    try:
        user_role = UserRole(role)
    except ValueError:
        user_role = UserRole.STUDENT

    user = await create_user(session, name, email, password, user_role)

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
        "isActive": user.is_active,
        "createdAt": user.created_at.isoformat()
    }
