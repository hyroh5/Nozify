"""Merge multiple heads

Revision ID: 21198248bda8
Revises: 411ef2eef622, 4316cb6f6240, 83e6302d123c
Create Date: 2025-11-22 14:26:41.395381

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21198248bda8'
down_revision: Union[str, Sequence[str], None] = ('411ef2eef622', '4316cb6f6240', '83e6302d123c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
