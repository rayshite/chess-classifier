"""
Точка входа для запуска приложения.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

import uvicorn

from config import settings


def check_database_connection():
    """Проверка подключения к БД перед запуском."""
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
    sync_engine = create_engine(sync_url)
    with sync_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    sync_engine.dispose()


def run_migrations():
    """Запуск миграций Alembic."""
    alembic_ini = Path(__file__).parent / "backend" / "db" / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini))

    os.chdir(alembic_ini.parent)
    command.upgrade(alembic_cfg, "head")


if __name__ == "__main__":
    try:
        check_database_connection()
        print("Подключение к БД установлено")
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        sys.exit(1)

    try:
        run_migrations()
        print("Миграции выполнены")
    except Exception as e:
        print(f"Ошибка выполнения миграций: {e}")
        sys.exit(1)

    from app import app
    uvicorn.run(app, host="127.0.0.1", port=8000)
