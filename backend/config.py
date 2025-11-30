"""
Конфигурация приложения.

Загружает настройки из переменных окружения.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class Settings:
    """Настройки приложения."""

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/chess_classifier"
    )

    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Время жизни токена авторизации (в секундах, по умолчанию 7 дней)
    AUTH_TOKEN_LIFETIME: int = int(os.getenv("AUTH_TOKEN_LIFETIME", 3600 * 24 * 7))

    # Лимит элементов на странице
    PAGE_LIMIT: int = int(os.getenv("PAGE_LIMIT", 10))

    BASE_DIR: Path = Path(__file__).parent.parent
    BACKEND_DIR: Path = Path(__file__).parent
    MODEL_PATH: Path = BACKEND_DIR / "model.keras"


settings = Settings()
