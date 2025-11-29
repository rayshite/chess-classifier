"""
Роутер для HTML страниц.
"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()

FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"

templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/login")
async def login_page(request: Request):
    """Страница входа"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/")
async def home(request: Request):
    """Главная страница"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/games/{game_id}")
async def game_page(request: Request, game_id: int):
    """Страница партии"""
    return templates.TemplateResponse("game.html", {"request": request})


@router.get("/users")
async def users_page(request: Request):
    """Страница управления пользователями"""
    return templates.TemplateResponse("users.html", {"request": request})
