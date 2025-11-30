from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from database import get_async_session
from models import UserRole
from routers import pages_router, games_router, users_router, auth_router
from services import get_user_by_id

app = FastAPI()

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.middleware("http")
async def admin_redirect_middleware(request: Request, call_next):
    """Редирект админа на страницу пользователей"""
    path = request.url.path

    # Пропускаем статику, API и страницы логина/users/profile
    if (path.startswith("/static") or
        path.startswith("/api") or
        path == "/login" or
        path == "/users" or
        path == "/profile"):
        return await call_next(request)

    # Проверяем авторизацию админа через cookie "auth" (JWT в cookie)
    auth_cookie = request.cookies.get("auth")
    if auth_cookie:
        try:
            import jwt
            from auth import SECRET
            payload = jwt.decode(
                auth_cookie,
                SECRET,
                algorithms=["HS256"],
                audience="fastapi-users:auth"
            )
            user_id = payload.get("sub")
            if user_id:
                async for session in get_async_session():
                    user = await get_user_by_id(session, int(user_id))
                    if user and user.role == UserRole.ADMIN:
                        return RedirectResponse(url="/users", status_code=302)
                    break
        except Exception:
            pass

    return await call_next(request)


# Подключаем роутеры
app.include_router(pages_router)
app.include_router(games_router)
app.include_router(users_router)
app.include_router(auth_router)
