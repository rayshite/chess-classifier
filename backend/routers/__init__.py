"""
Роутеры приложения.
"""

from .pages import router as pages_router
from .games import router as games_router
from .users import router as users_router
from .auth import router as auth_router

__all__ = [
    "pages_router",
    "games_router",
    "users_router",
    "auth_router",
]
