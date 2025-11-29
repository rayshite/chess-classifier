"""
Роутер для API игр.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from auth import current_active_user
from classifier import predict_all_squares
from database import get_async_session
from models import GameStatus, User, UserRole
from services import (
    get_games_list,
    get_games_count,
    get_game_by_id,
    create_snapshot,
    delete_last_snapshot,
    update_game_status,
    process_board_image,
    predictions_to_fen,
)

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("")
async def get_games(
    page: int = 1,
    limit: int = 2,
    status: str | None = None,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Получить список партий с пагинацией и фильтрацией"""
    page = max(1, page)
    limit = min(max(1, limit), 100)

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
    game_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Получить информацию о партии по ID"""
    game = await get_game_by_id(session, game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Партия не найдена")

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
    game_id: int,
    image: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session)
):
    """Добавить новый снепшот к партии"""
    game = await get_game_by_id(session, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Партия не найдена")

    contents = await image.read()

    try:
        squares = process_board_image(contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    predictions = predict_all_squares(squares)
    position = predictions_to_fen(predictions)
    snapshot = await create_snapshot(session, game_id, position)
    move_number = len(game.snapshots) + 1

    return {
        "id": snapshot.id,
        "moveNumber": move_number,
        "position": snapshot.position,
        "createdAt": snapshot.created_at.isoformat()
    }


@router.delete("/{game_id}/snapshots/last")
async def remove_last_snapshot(
    game_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Удалить последний снепшот партии"""
    game = await get_game_by_id(session, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Партия не найдена")

    snapshot = await delete_last_snapshot(session, game_id)

    if not snapshot:
        raise HTTPException(status_code=404, detail="Снепшотов нет")

    return {"message": "Снепшот удалён", "id": snapshot.id}


@router.patch("/{game_id}/status")
async def change_game_status(
    game_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Переключить статус партии"""
    game = await get_game_by_id(session, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Партия не найдена")

    new_status = GameStatus.FINISHED if game.status == GameStatus.IN_PROGRESS else GameStatus.IN_PROGRESS
    game = await update_game_status(session, game_id, new_status)

    return {"status": game.status.value}
