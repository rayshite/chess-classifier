"""
Сервис для работы с пользователями.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, UserRole


async def get_users_list(
    session: AsyncSession,
    role: UserRole | None = None,
    limit: int = 10,
    offset: int = 0
):
    """
    Получить список пользователей с фильтрацией и пагинацией.

    Args:
        session: Сессия БД
        role: Фильтр по роли (опционально)
        limit: Максимальное количество записей
        offset: Смещение для пагинации

    Returns:
        Список пользователей
    """
    query = (
        select(User)
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if role:
        query = query.where(User.role == role)

    result = await session.execute(query)
    users = result.scalars().all()

    return users


async def get_users_count(session: AsyncSession, role: UserRole | None = None):
    """
    Получить количество пользователей.

    Args:
        session: Сессия БД
        role: Фильтр по роли (опционально)

    Returns:
        Количество пользователей
    """
    query = select(func.count(User.id))

    if role:
        query = query.where(User.role == role)

    result = await session.execute(query)
    count = result.scalar()

    return count
