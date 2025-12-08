"""Add fastapi-users fields (is_superuser, is_verified)

Revision ID: 002
Revises: 001
Create Date: 2025-01-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем колонки, требуемые fastapi-users
    op.add_column('users', sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'is_verified')
    op.drop_column('users', 'is_superuser')
