"""
Общая конфигурация pytest.

Добавляет backend в sys.path для всех тестов.
"""

import sys
from pathlib import Path

# Добавляем backend в sys.path для корректных импортов
BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
