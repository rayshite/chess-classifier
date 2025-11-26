"""Initial migration - users, games, snapshots

Revision ID: 001
Revises:
Create Date: 2025-01-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM


revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role = ENUM('student', 'teacher', 'admin', name='user_role', create_type=False)
    game_status = ENUM('in_progress', 'finished', name='game_status', create_type=False)

    user_role.create(op.get_bind(), checkfirst=True)
    game_status.create(op.get_bind(), checkfirst=True)

    # Таблица пользователей
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('role', user_role, nullable=False, server_default='student'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Таблица партий
    op.create_table(
        'games',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('status', game_status, nullable=False, server_default='in_progress'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('player1_id', sa.Integer(), nullable=False),
        sa.Column('player2_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['player1_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['player2_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Таблица снимков состояний партии
    op.create_table(
        'snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Text(), nullable=False),
        sa.Column('move_number', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Индексы
    op.create_index('ix_games_player1_id', 'games', ['player1_id'])
    op.create_index('ix_games_player2_id', 'games', ['player2_id'])
    op.create_index('ix_games_status', 'games', ['status'])
    op.create_index('ix_snapshots_game_id', 'snapshots', ['game_id'])


def downgrade() -> None:
    op.drop_index('ix_snapshots_game_id', table_name='snapshots')
    op.drop_index('ix_games_status', table_name='games')
    op.drop_index('ix_games_player2_id', table_name='games')
    op.drop_index('ix_games_player1_id', table_name='games')

    op.drop_table('snapshots')
    op.drop_table('games')
    op.drop_table('users')

    sa.Enum(name='gamestatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
