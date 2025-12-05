"""
Роутер для аутентификации (fastapi-users).
"""

from fastapi import APIRouter, Depends

from auth import auth_backend, current_active_user, fastapi_users
from models import User
from schemas import UserCreate, UserRead, UserUpdate

router = APIRouter()

# Роуты логина/логаута
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/api/auth",
    tags=["auth"],
)


@router.get("/api/current_user")
async def get_current_user(user: User = Depends(current_active_user)):
    """Получить текущего пользователя."""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value
    }
