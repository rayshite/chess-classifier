from pathlib import Path

from fastapi import Depends, FastAPI, UploadFile, File, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from classifier import predict_all_squares
from database import get_async_session
from fastapi.responses import JSONResponse
from services import get_games_list, get_games_count, get_game_by_id, create_snapshot, delete_last_snapshot, update_game_status, process_board_image, predictions_to_fen, get_users_list, get_users_count, get_user_by_email, get_user_by_id, create_user, authenticate_user

app = FastAPI()

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

@app.get("/login")
async def login_page(request: Request):
    """Страница входа"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/")
async def home(request: Request):
    """Главная страница - отдает пустой шаблон, данные загружаются через API"""
    return templates.TemplateResponse("index.html", {"request": request})

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
    return templates.TemplateResponse("game.html", {"request": request})

@app.get("/users")
async def users_page(request: Request):
    """Страница управления пользователями"""
    return templates.TemplateResponse("users.html", {"request": request})

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


@app.post("/api/users")
async def create_new_user(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    """API endpoint для создания нового пользователя"""
    from models import UserRole

    data = await request.json()

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    role = data.get("role", "student")

    # Валидация
    if not name:
        raise HTTPException(status_code=400, detail="Имя обязательно")
    if not email:
        raise HTTPException(status_code=400, detail="Email обязателен")
    if not password:
        raise HTTPException(status_code=400, detail="Пароль обязателен")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Пароль должен быть не менее 6 символов")

    # Проверяем, что email не занят
    existing_user = await get_user_by_email(session, email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    # Преобразуем роль
    try:
        user_role = UserRole(role)
    except ValueError:
        user_role = UserRole.STUDENT

    # Создаем пользователя
    user = await create_user(session, name, email, password, user_role)

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
        "isActive": user.is_active,
        "createdAt": user.created_at.isoformat()
    }


@app.post("/api/login")
async def login(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    """API endpoint для аутентификации пользователя"""
    data = await request.json()

    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email и пароль обязательны")

    user = await authenticate_user(session, email, password)

    if not user:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    # Создаем ответ с cookie
    response = JSONResponse(content={
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value
    })

    # Устанавливаем cookie с ID пользователя (простая сессия)
    response.set_cookie(
        key="user_id",
        value=str(user.id),
        httponly=True,
        max_age=60 * 60 * 24 * 7  # 7 дней
    )

    return response


@app.post("/api/logout")
async def logout():
    """API endpoint для выхода из системы"""
    response = JSONResponse(content={"message": "Выход выполнен"})
    response.delete_cookie("user_id")
    return response


@app.get("/api/current_user")
async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    """API endpoint для получения текущего пользователя"""
    user_id = request.cookies.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="Не авторизован")

    try:
        user_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Не авторизован")

    user = await get_user_by_id(session, user_id)

    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value
    }