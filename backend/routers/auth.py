"""
Роутер для аутентификации (fastapi-users).
"""

from fastapi import APIRouter, Depends

from auth import auth_backend, fastapi_users

router = APIRouter()

# Роуты логина/логаута
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/api/auth",
    tags=["auth"],
)
