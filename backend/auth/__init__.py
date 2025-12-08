"""
Модуль аутентификации.
"""

from .auth import (
    fastapi_users,
    auth_backend,
    current_active_user,
    current_active_user_optional,
    require_admin,
    get_user_manager,
)

__all__ = [
    "fastapi_users",
    "auth_backend",
    "current_active_user",
    "current_active_user_optional",
    "require_admin",
    "get_user_manager",
]
