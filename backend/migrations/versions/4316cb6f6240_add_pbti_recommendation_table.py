"""add pbti_recommendation table

Revision ID: 4316cb6f6240
Revises: 1a17c6ab329d
Create Date: 2025-11-22 13:54:34.286081

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4316cb6f6240'
down_revision: Union[str, Sequence[str], None] = '52fa5f0732dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
