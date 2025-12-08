from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import settings
from routers import pages_router, games_router, users_router, auth_router

app = FastAPI()

app.mount("/static", StaticFiles(directory=settings.FRONTEND_DIR), name="static")


# Подключаем роутеры
app.include_router(pages_router)
app.include_router(games_router)
app.include_router(users_router)
app.include_router(auth_router)
