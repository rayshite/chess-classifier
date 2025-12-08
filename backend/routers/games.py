"""
Роутер для API игр.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from auth import current_active_user
from config import settings
from db import get_async_session, GameStatus, User, UserRole, GameCreate
from services import (
    get_games_list,
    get_games_count,
    get_game_by_id,
    create_game,
    create_snapshot,
    delete_last_snapshot,
    update_game_status,
    process_board_image,
    predictions_to_fen,
    predict_all_squares,
)

router = APIRouter(prefix="/api/games", tags=["games"])


async def get_game_with_access_check(
    game_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Получить партию с проверкой доступа."""
    game = await get_game_by_id(session, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Партия не найдена")

    if user.role == UserRole.STUDENT:
        if game.player1_id != user.id and game.player2_id != user.id:
            raise HTTPException(status_code=403, detail="Нет доступа к этой партии")

    return game


@router.post("")
async def create_new_game(
    data: GameCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Создать новую партию."""
    # Ученик должен быть одним из игроков
    if user.role == UserRole.STUDENT:
        if data.player1Id != user.id and data.player2Id != user.id:
            raise HTTPException(status_code=400, detail="Вы должны быть одним из игроков")

    game = await create_game(session, data.title, data.player1Id, data.player2Id)

    return {
        "id": game.id,
        "title": game.title,
        "status": game.status.value,
        "player1Id": game.player1_id,
        "player2Id": game.player2_id,
        "createdAt": game.created_at.isoformat()
    }


@router.get("")
async def get_games(
    page: int = 1,
    status: str | None = None,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Получить список партий с пагинацией и фильтрацией"""
    page = max(1, page)
    limit = settings.PAGE_LIMIT

    status_filter = None
    if status and status != 'all':
        try:
            status_filter = GameStatus(status)
        except ValueError:
            pass

    # Ученики видят только свои партии
    user_id_filter = user.id if user.role == UserRole.STUDENT else None

    offset = (page - 1) * limit

    games = await get_games_list(session, status=status_filter, user_id=user_id_filter, limit=limit, offset=offset)
    total_count = await get_games_count(session, status=status_filter, user_id=user_id_filter)
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

    games_data = [
        {
            "id": game.id,
            "title": game.title,
            "status": game.status.value,
            "player1": {"id": game.player1.id, "name": game.player1.name},
            "player2": {"id": game.player2.id, "name": game.player2.name},
            "snapshotCount": len(game.snapshots),
            "createdAt": game.created_at.isoformat()
        }
        for game in games
    ]

    return {
        "games": games_data,
        "pagination": {
            "currentPage": page,
            "totalPages": total_pages,
            "totalCount": total_count,
            "limit": limit
        }
    }


@router.get("/{game_id}")
async def get_game(
    game = Depends(get_game_with_access_check)
):
    """Получить информацию о партии по ID"""
    snapshots_data = [
        {
            "id": snapshot.id,
            "moveNumber": idx + 1,
            "position": snapshot.position,
            "createdAt": snapshot.created_at.isoformat()
        }
        for idx, snapshot in enumerate(game.snapshots)
    ]

    return {
        "id": game.id,
        "title": game.title,
        "status": game.status.value,
        "player1": {"id": game.player1.id, "name": game.player1.name},
        "player2": {"id": game.player2.id, "name": game.player2.name},
        "snapshotCount": len(game.snapshots),
        "snapshots": snapshots_data,
        "createdAt": game.created_at.isoformat()
    }


@router.post("/{game_id}/snapshots")
async def add_snapshot(
    image: UploadFile = File(...),
    game = Depends(get_game_with_access_check),
    session: AsyncSession = Depends(get_async_session)
):
    """Добавить новый снепшот к партии"""
    if game.status != GameStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Партия завершена")

    contents = await image.read()

    try:
        squares = process_board_image(contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    predictions = predict_all_squares(squares)
    position = predictions_to_fen(predictions)
    snapshot = await create_snapshot(session, game.id, position)
    move_number = len(game.snapshots) + 1

    return {
        "id": snapshot.id,
        "moveNumber": move_number,
        "position": snapshot.position,
        "createdAt": snapshot.created_at.isoformat()
    }


@router.delete("/{game_id}/snapshots/last")
async def remove_last_snapshot(
    game = Depends(get_game_with_access_check),
    session: AsyncSession = Depends(get_async_session)
):
    """Удалить последний снепшот партии"""
    if game.status != GameStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Партия завершена")

    snapshot = await delete_last_snapshot(session, game.id)

    if not snapshot:
        raise HTTPException(status_code=404, detail="Снепшотов нет")

    return {"message": "Снепшот удалён", "id": snapshot.id}


@router.patch("/{game_id}/status")
async def change_game_status(
    game = Depends(get_game_with_access_check),
    session: AsyncSession = Depends(get_async_session)
):
    """Переключить статус партии"""
    new_status = GameStatus.FINISHED if game.status == GameStatus.IN_PROGRESS else GameStatus.IN_PROGRESS
    game = await update_game_status(session, game.id, new_status)

    return {"status": game.status.value}
