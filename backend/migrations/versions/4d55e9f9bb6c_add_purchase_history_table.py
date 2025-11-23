"""add purchase_history table

Revision ID: 4d55e9f9bb6c
Revises: 38b8ba9ecb9e
Create Date: 2025-11-23 22:36:28.607091

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import BINARY

# revision identifiers, used by Alembic.
revision = 'add_purchase_history'
down_revision = '38b8ba9ecb9e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'purchase_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', BINARY(16), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('perfume_id', BINARY(16), sa.ForeignKey('perfume.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('purchase_date', sa.Date(), nullable=True),

        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        sa.Index('ix_purchase_user_date', 'user_id', 'purchase_date'),
        sa.Index('ix_purchase_perfume', 'perfume_id'),
    )


def downgrade() -> None:
    op.drop_table('purchase_history')
