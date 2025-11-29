"""
Сервис для работы с пользователями.
"""

import hashlib

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, UserRole


def hash_password(password: str) -> str:
    """Хеширование пароля с использованием SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


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


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """
    Получить пользователя по email.

    Args:
        session: Сессия БД
        email: Email пользователя

    Returns:
        Пользователь или None
    """
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    name: str,
    email: str,
    password: str,
    role: UserRole = UserRole.STUDENT
) -> User:
    """
    Создать нового пользователя.

    Args:
        session: Сессия БД
        name: Имя пользователя
        email: Email
        password: Пароль (будет захеширован)
        role: Роль пользователя

    Returns:
        Созданный пользователь
    """
    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
        role=role
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user
