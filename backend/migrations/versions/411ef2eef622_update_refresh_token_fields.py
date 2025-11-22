"""update refresh_token fields

Revision ID: 411ef2eef622
Revises: 1a17c6ab329d
Create Date: 2025-11-22 12:33:32.151127

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '411ef2eef622'
down_revision: Union[str, Sequence[str], None] = '1a17c6ab329d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.alter_column(
        "refresh_token",
        "expires_at",
        existing_type=sa.DateTime(),
        nullable=True
    )

def downgrade() -> None:
    op.alter_column(
        "refresh_token",
        "expires_at",
        existing_type=sa.DateTime(),
        nullable=False
    )
