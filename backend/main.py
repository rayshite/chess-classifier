from pathlib import Path

from fastapi import Depends, FastAPI, UploadFile, File, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from board_service import process_board_image
from classifier import predict_all_squares
from database import get_async_session
from services import get_games_list, get_games_count

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

@app.post("/api/predict")
async def predict(image: UploadFile = File(...)):
    """
    Принимает изображение шахматной доски и возвращает предсказания.
    """
    contents = await image.read()

    try:
        squares = process_board_image(contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Классификация каждой клетки
    predictions = predict_all_squares(squares)

    return {
        "predictions": predictions
    }