"""Create admin user

Revision ID: 003
Revises: 002
Create Date: 2025-01-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Пароль: password123 (argon2 хеш для pwdlib)
    op.execute("""
        INSERT INTO users (email, hashed_password, name, role, is_active, is_superuser, is_verified)
        VALUES (
            'admin@example.com',
            '$argon2id$v=19$m=65536,t=3,p=4$t+swrG6tKCnNCDLJkDWmSw$2BJ6tBr1nD3MtdyVH/7X8aZwEXOhMAy88b74KxVYndE',
            'Администратор',
            'admin',
            true,
            true,
            true
        )
        ON CONFLICT (email) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM users WHERE email = 'admin@example.com'")
