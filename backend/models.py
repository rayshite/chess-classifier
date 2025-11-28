"""
Модели базы данных.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class UserRole(str, enum.Enum):
    """Роли пользователей."""
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class GameStatus(str, enum.Enum):
    """Статусы партии."""
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class User(Base):
    """
    Пользователь системы.

    Роли:
    - student: видит только свои партии (где он player1 или player2)
    - teacher: видит все партии, может редактировать и удалять
    - admin: управление пользователями
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x], name='user_role'),
        default=UserRole.STUDENT,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Связи
    games_as_player1: Mapped[list["Game"]] = relationship(
        back_populates="player1",
        foreign_keys="Game.player1_id"
    )
    games_as_player2: Mapped[list["Game"]] = relationship(
        back_populates="player2",
        foreign_keys="Game.player2_id"
    )


class Game(Base):
    """
    Шахматная партия.

    Участвуют два игрока (player1 и player2).
    Оба могут редактировать партию.
    Содержит список снепшотов (позиций доски).
    """
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[GameStatus] = mapped_column(
        Enum(GameStatus, values_callable=lambda x: [e.value for e in x], name='game_status'),
        default=GameStatus.IN_PROGRESS,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    player1_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    player2_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Связи
    player1: Mapped["User"] = relationship(
        back_populates="games_as_player1",
        foreign_keys=[player1_id]
    )
    player2: Mapped["User"] = relationship(
        back_populates="games_as_player2",
        foreign_keys=[player2_id]
    )
    snapshots: Mapped[list["Snapshot"]] = relationship(
        back_populates="game",
        cascade="all, delete-orphan",
        order_by="Snapshot.created_at"
    )


class Snapshot(Base):
    """
    Снепшот (снимок) позиции на доске.

    Хранит позицию в формате JSON (словарь клетка -> фигура).
    Например: {"a1": "wR", "b1": "wN", ...}
    """
    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False
    )
    position: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Связи
    game: Mapped["Game"] = relationship(back_populates="snapshots")
