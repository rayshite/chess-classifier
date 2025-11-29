"""
Слой сервисов для бизнес-логики.
"""

from .game_service import get_game_by_id, get_games_count, get_games_list, create_snapshot, delete_last_snapshot, update_game_status
from .board_service import process_board_image, predictions_to_fen
from .user_service import get_users_list, get_users_count, get_user_by_email, get_user_by_id, create_user, authenticate_user

__all__ = [
    "get_games_list",
    "get_game_by_id",
    "get_games_count",
    "create_snapshot",
    "delete_last_snapshot",
    "update_game_status",
    "process_board_image",
    "predictions_to_fen",
    "get_users_list",
    "get_users_count",
    "get_user_by_email",
    "get_user_by_id",
    "create_user",
    "authenticate_user",
]