"""
Роутер для API пользователей.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from models import UserRole
from services import get_users_list, get_users_count

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
