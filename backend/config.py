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

    # Использовать Secure cookie (только HTTPS). По умолчанию True для безопасности.
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "true").lower() == "true"

    # Лимит элементов на странице
    PAGE_LIMIT: int = int(os.getenv("PAGE_LIMIT", 10))

    BASE_DIR: Path = Path(__file__).parent.parent
    BACKEND_DIR: Path = Path(__file__).parent
    FRONTEND_DIR: Path = BASE_DIR / "frontend"
    TEMPLATES_DIR: Path = FRONTEND_DIR / "templates"
    MODEL_PATH: Path = BACKEND_DIR / "services" / "ml" / "model.keras"


settings = Settings()
