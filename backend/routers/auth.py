"""
Роутер для аутентификации.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from services import authenticate_user, get_user_by_id

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/login")
async def login(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    """Аутентификация пользователя"""
    data = await request.json()

    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email и пароль обязательны")

    user = await authenticate_user(session, email, password)

    if not user:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    response = JSONResponse(content={
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value
    })

    response.set_cookie(
        key="user_id",
        value=str(user.id),
        httponly=True,
        max_age=60 * 60 * 24 * 7  # 7 дней
    )

    return response


@router.post("/logout")
async def logout():
    """Выход из системы"""
    response = JSONResponse(content={"message": "Выход выполнен"})
    response.delete_cookie("user_id")
    return response


@router.get("/current_user")
async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    """Получить текущего пользователя"""
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
