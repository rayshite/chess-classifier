"""
Конфигурация fastapi-users.
"""

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.authentication import AuthenticationBackend, CookieTransport, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_async_session
from models import User


# Секретный ключ для JWT
SECRET = settings.SECRET_KEY or "CHANGE_ME_IN_PRODUCTION"


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """Получить адаптер базы данных для пользователей."""
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """Менеджер пользователей."""
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """Получить менеджер пользователей."""
    yield UserManager(user_db)


# Транспорт через cookie
cookie_transport = CookieTransport(cookie_name="auth", cookie_max_age=3600 * 24 * 7)


def get_jwt_strategy() -> JWTStrategy:
    """Стратегия JWT."""
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600 * 24 * 7)


# Backend аутентификации
auth_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)


# Главный объект fastapi-users
fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])


# Зависимости для получения текущего пользователя
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
