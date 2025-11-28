"""
Сервис для работы с партиями.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Game, GameStatus


async def get_games_list(
    session: AsyncSession,
    status: GameStatus | None = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Получить список партий с фильтрацией и пагинацией.

    Args:
        session: Сессия БД
        status: Фильтр по статусу (опционально)
        limit: Максимальное количество записей
        offset: Смещение для пагинации

    Returns:
        Список партий с загруженными связями (player1, player2, snapshots)
    """
    query = (
        select(Game)
        .options(
            selectinload(Game.player1),
            selectinload(Game.player2),
            selectinload(Game.snapshots)
        )
        .order_by(Game.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if status:
        query = query.where(Game.status == status.value)

    result = await session.execute(query)
    games = result.scalars().all()

    return games


async def get_game_by_id(session: AsyncSession, game_id: int):
    """
    Получить партию по ID.

    Args:
        session: Сессия БД
        game_id: ID партии

    Returns:
        Партия или None, если не найдена
    """
    query = (
        select(Game)
        .options(
            selectinload(Game.player1),
            selectinload(Game.player2),
            selectinload(Game.snapshots)
        )
        .where(Game.id == game_id)
    )

    result = await session.execute(query)
    game = result.scalar_one_or_none()

    return game


async def get_games_count(session: AsyncSession, status: GameStatus | None = None):
    """
    Получить количество партий.

    Args:
        session: Сессия БД
        status: Фильтр по статусу (опционально)

    Returns:
        Количество партий
    """
    query = select(func.count(Game.id))

    if status:
        query = query.where(Game.status == status.value)

    result = await session.execute(query)
    count = result.scalar()

    return count