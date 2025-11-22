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

    BASE_DIR: Path = Path(__file__).parent.parent
    BACKEND_DIR: Path = Path(__file__).parent
    MODEL_PATH: Path = BACKEND_DIR / "model.keras"


settings = Settings()
