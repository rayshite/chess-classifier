"""
Сервис для работы с партиями.
"""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db import Game, GameStatus, Snapshot


async def create_game(
        session: AsyncSession,
        title: str,
        player1_id: int,
        player2_id: int
) -> Game:
    """
    Создать новую партию.

    Args:
        session: Сессия БД
        title: Название партии
        player1_id: ID первого игрока (белые)
        player2_id: ID второго игрока (чёрные)

    Returns:
        Созданная партия
    """
    game = Game(
        title=title,
        player1_id=player1_id,
        player2_id=player2_id,
        status=GameStatus.IN_PROGRESS
    )
    session.add(game)
    await session.commit()
    await session.refresh(game)

    return game


async def get_games_list(
        session: AsyncSession,
        status: GameStatus | None = None,
        user_id: int | None = None,
        limit: int = 100,
        offset: int = 0
):
    """
    Получить список партий с фильтрацией и пагинацией.

    Args:
        session: Сессия БД
        status: Фильтр по статусу (опционально)
        user_id: ID пользователя для фильтрации (только его партии)
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

    if user_id:
        query = query.where(or_(Game.player1_id == user_id, Game.player2_id == user_id))

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


async def get_games_count(session: AsyncSession, status: GameStatus | None = None, user_id: int | None = None):
    """
    Получить количество партий.

    Args:
        session: Сессия БД
        status: Фильтр по статусу (опционально)
        user_id: ID пользователя для фильтрации (только его партии)

    Returns:
        Количество партий
    """
    query = select(func.count(Game.id))

    if status:
        query = query.where(Game.status == status.value)

    if user_id:
        query = query.where(or_(Game.player1_id == user_id, Game.player2_id == user_id))

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
