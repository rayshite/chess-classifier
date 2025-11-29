"""
Сервис для работы с партиями.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Game, GameStatus, Snapshot


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


async def create_snapshot(session: AsyncSession, game_id: int, position: str):
    """
    Создать новый снепшот для партии.

    Args:
        session: Сессия БД
        game_id: ID партии
        position: Позиция в формате FEN

    Returns:
        Созданный снепшот
    """
    snapshot = Snapshot(game_id=game_id, position=position)
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)

    return snapshot


async def delete_last_snapshot(session: AsyncSession, game_id: int) -> Snapshot | None:
    """
    Удалить последний снепшот партии.

    Args:
        session: Сессия БД
        game_id: ID партии

    Returns:
        Удалённый снепшот или None, если снепшотов нет
    """
    # Находим последний снепшот по дате создания
    query = (
        select(Snapshot)
        .where(Snapshot.game_id == game_id)
        .order_by(Snapshot.created_at.desc())
        .limit(1)
    )

    result = await session.execute(query)
    snapshot = result.scalar_one_or_none()

    if snapshot:
        await session.delete(snapshot)
        await session.commit()

    return snapshot


async def update_game_status(session: AsyncSession, game_id: int, status: GameStatus) -> Game | None:
    """
    Обновить статус партии.

    Args:
        session: Сессия БД
        game_id: ID партии
        status: Новый статус

    Returns:
        Обновлённая партия или None, если не найдена
    """
    game = await get_game_by_id(session, game_id)

    if game:
        game.status = status
        await session.commit()
        await session.refresh(game)

    return game