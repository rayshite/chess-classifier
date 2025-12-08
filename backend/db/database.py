"""
Настройка подключения к базе данных.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass


# Создаём асинхронный движок SQLAlchemy
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
)

# Фабрика сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session():
    """Dependency для получения сессии БД."""
    async with async_session_maker() as session:
        yield session
