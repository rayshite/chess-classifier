"""
Слой сервисов для бизнес-логики.
"""

from .game_service import get_game_by_id, get_games_count, get_games_list

__all__ = [
    "get_games_list",
    "get_game_by_id",
    "get_games_count",
]