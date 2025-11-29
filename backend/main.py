from pathlib import Path

from fastapi import Depends, FastAPI, UploadFile, File, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from classifier import predict_all_squares
from database import get_async_session
from services import get_games_list, get_games_count, get_game_by_id, create_snapshot, delete_last_snapshot, update_game_status, process_board_image, predictions_to_fen, get_users_list, get_users_count

app = FastAPI()

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

@app.get("/")
async def home(request: Request):
    """Главная страница - отдает пустой шаблон, данные загружаются через API"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user_name": "Иван Петров"  # TODO: получать из сессии
    })

@app.get("/api/games")
async def get_games(
    page: int = 1,
    limit: int = 2,
    status: str | None = None,
    session: AsyncSession = Depends(get_async_session)
):
    """API endpoint для получения списка партий с пагинацией и фильтрацией"""
    # Валидация параметров
    page = max(1, page)
    limit = min(max(1, limit), 100)

    # Преобразование статуса в enum
    from models import GameStatus
    status_filter = None
    if status and status != 'all':
        try:
            status_filter = GameStatus(status)
        except ValueError:
            pass

    offset = (page - 1) * limit

    # Получаем партии и общее количество
    games = await get_games_list(session, status=status_filter, limit=limit, offset=offset)
    total_count = await get_games_count(session, status=status_filter)
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

    # Преобразуем данные в JSON-сериализуемый формат
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

@app.get("/games/{game_id}")
async def game_page(request: Request, game_id: int):
    return templates.TemplateResponse("game.html", {
        "request": request,
        "user_name": "Иван Петров"
    })

@app.get("/users")
async def users_page(request: Request):
    """Страница управления пользователями"""
    return templates.TemplateResponse("users.html", {
        "request": request,
        "user_name": "Иван Петров"
    })

@app.get("/api/games/{game_id}")
async def get_game(
    game_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """API endpoint для получения информации о партии по ID"""
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

@app.post("/api/games/{game_id}/snapshots")
async def add_snapshot(
    game_id: int,
    image: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Добавить новый снепшот к партии.
    Принимает изображение шахматной доски, распознает позицию и сохраняет снепшот.
    """
    # Проверяем существование партии
    game = await get_game_by_id(session, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Партия не найдена")

    # Читаем изображение
    contents = await image.read()

    try:
        squares = process_board_image(contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Классификация каждой клетки
    predictions = predict_all_squares(squares)

    # Преобразуем предсказания в FEN-позицию
    position = predictions_to_fen(predictions)

    # Создаем снепшот
    snapshot = await create_snapshot(session, game_id, position)

    # Вычисляем номер хода
    move_number = len(game.snapshots) + 1

    return {
        "id": snapshot.id,
        "moveNumber": move_number,
        "position": snapshot.position,
        "createdAt": snapshot.created_at.isoformat()
    }


@app.delete("/api/games/{game_id}/snapshots/last")
async def remove_last_snapshot(
    game_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Удалить последний снепшот партии.
    """
    # Проверяем существование партии
    game = await get_game_by_id(session, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Партия не найдена")

    # Удаляем последний снепшот
    snapshot = await delete_last_snapshot(session, game_id)

    if not snapshot:
        raise HTTPException(status_code=404, detail="Снепшотов нет")

    return {"message": "Снепшот удалён", "id": snapshot.id}


@app.patch("/api/games/{game_id}/status")
async def change_game_status(
    game_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Переключить статус партии.
    Если 'in_progress' -> 'finished', если 'finished' -> 'in_progress'.
    """
    from models import GameStatus

    # Получаем партию
    game = await get_game_by_id(session, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Партия не найдена")

    # Переключаем статус
    new_status = GameStatus.FINISHED if game.status == GameStatus.IN_PROGRESS else GameStatus.IN_PROGRESS

    # Обновляем статус
    game = await update_game_status(session, game_id, new_status)

    return {"status": game.status.value}


@app.get("/api/users")
async def get_users(
    page: int = 1,
    limit: int = 10,
    role: str | None = None,
    session: AsyncSession = Depends(get_async_session)
):
    """API endpoint для получения списка пользователей с пагинацией и фильтрацией"""
    from models import UserRole

    # Валидация параметров
    page = max(1, page)
    limit = min(max(1, limit), 100)

    # Преобразование роли в enum
    role_filter = None
    if role and role != 'all':
        try:
            role_filter = UserRole(role)
        except ValueError:
            pass

    offset = (page - 1) * limit

    # Получаем пользователей и общее количество
    users = await get_users_list(session, role=role_filter, limit=limit, offset=offset)
    total_count = await get_users_count(session, role=role_filter)
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

    # Преобразуем данные в JSON-сериализуемый формат
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