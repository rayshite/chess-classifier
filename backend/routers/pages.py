"""
Роутер для HTML страниц.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from auth import current_active_user_optional
from config import settings
from database import get_async_session
from models import User, UserRole
from services import get_game_by_id

router = APIRouter()

templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)


@router.get("/login")
async def login_page(request: Request):
    """Страница входа"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/")
async def home(request: Request, user: User | None = Depends(current_active_user_optional)):
    """Главная страница"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user.role == UserRole.ADMIN:
        return RedirectResponse(url="/users", status_code=302)
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/games/{game_id}")
async def game_page(
    request: Request,
    game_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User | None = Depends(current_active_user_optional)
):
    """Страница партии"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user.role == UserRole.ADMIN:
        return RedirectResponse(url="/users", status_code=302)

    game = await get_game_by_id(session, game_id)

    if not game:
        return RedirectResponse(url="/", status_code=302)

    # Ученики могут видеть только свои партии
    if user.role == UserRole.STUDENT:
        if game.player1_id != user.id and game.player2_id != user.id:
            return RedirectResponse(url="/", status_code=302)

    return templates.TemplateResponse("game.html", {"request": request})


@router.get("/users")
async def users_page(request: Request, user: User | None = Depends(current_active_user_optional)):
    """Страница управления пользователями"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user.role != UserRole.ADMIN:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("users.html", {"request": request})


@router.get("/profile")
async def profile_page(request: Request, user: User | None = Depends(current_active_user_optional)):
    """Страница профиля пользователя"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("profile.html", {"request": request})
