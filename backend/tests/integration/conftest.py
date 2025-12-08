"""
Конфигурация pytest для интеграционных тестов.

Использует Testcontainers для PostgreSQL.
"""

import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

os.environ["TESTCONTAINERS_RYUK_DISABLED"] = "true"

from db import Base, get_async_session, User, UserRole


@pytest.fixture(scope="session")
def postgres_container():
    """Запускаем PostgreSQL контейнер для тестов."""
    postgres = PostgresContainer("postgres:15")
    postgres.start()
    yield postgres
    postgres.stop()


@pytest.fixture(scope="session")
def database_url(postgres_container):
    """Формируем URL для подключения к тестовой БД."""
    url = postgres_container.get_connection_url()
    return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")


@pytest.fixture(scope="session")
def test_engine(database_url):
    """Создаём тестовый движок SQLAlchemy."""
    return create_async_engine(database_url, echo=False)


@pytest.fixture(scope="session")
def async_session_maker(test_engine):
    """Фабрика сессий."""
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def setup_database(test_engine):
    """Создаём таблицы в тестовой БД."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def test_user(async_session_maker, setup_database) -> User:
    """Создаём тестового пользователя (один раз на сессию)."""
    from pwdlib import PasswordHash

    password_hash = PasswordHash.recommended()
    hashed_password = password_hash.hash("testpassword123")

    async with async_session_maker() as session:
        user = User(
            email="test@example.com",
            hashed_password=hashed_password,
            name="Test User",
            role=UserRole.STUDENT,
            is_active=True,
            is_superuser=False,
            is_verified=True,
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return User(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            is_verified=user.is_verified,
        )


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def teacher_user(async_session_maker, setup_database) -> User:
    """Создаём тестового учителя (один раз на сессию)."""
    from pwdlib import PasswordHash

    password_hash = PasswordHash.recommended()
    hashed_password = password_hash.hash("teacherpass123")

    async with async_session_maker() as session:
        user = User(
            email="teacher@example.com",
            hashed_password=hashed_password,
            name="Test Teacher",
            role=UserRole.TEACHER,
            is_active=True,
            is_superuser=False,
            is_verified=True,
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return User(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            is_verified=user.is_verified,
        )


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def admin_user(async_session_maker, setup_database) -> User:
    """Создаём тестового администратора (один раз на сессию)."""
    from pwdlib import PasswordHash

    password_hash = PasswordHash.recommended()
    hashed_password = password_hash.hash("adminpass123")

    async with async_session_maker() as session:
        user = User(
            email="admin@example.com",
            hashed_password=hashed_password,
            name="Test Admin",
            role=UserRole.ADMIN,
            is_active=True,
            is_superuser=True,
            is_verified=True,
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return User(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            is_verified=user.is_verified,
        )


@pytest_asyncio.fixture(loop_scope="session")
async def client(async_session_maker, setup_database) -> AsyncGenerator[AsyncClient, None]:
    """Создаём тестовый HTTP клиент."""
    from app import app

    async def override_get_session():
        async with async_session_maker() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
