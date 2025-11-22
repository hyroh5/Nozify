"""create pbti_recommendation table (final attempt)

Revision ID: f9b5ff9fcaf7
Revises: 076e0e2baf47
Create Date: 2025-11-22 14:32:01.132844

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
# sqlalchemy.dialects.mysql은 더 이상 필요하지 않아 제거했습니다.

# revision identifiers, used by Alembic.
revision: str = 'f9b5ff9fcaf7'
down_revision: Union[str, Sequence[str], None] = '076e0e2baf47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 'pbti_recommendation' 테이블 생성
    op.create_table(
        'pbti_recommendation',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('type_code', sa.String(length=50), nullable=False),

        # 💡 [최종 수정] sa.Binary(소문자) 대신 sa.BINARY(대문자) 사용
        sa.Column('perfume_id', sa.BINARY(length=16), nullable=False),

        sa.Column('match_score', sa.Float(), nullable=False),

        # TimestampMixin 필드
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),

        # 기본 키 및 외래 키 설정
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['perfume_id'], ['perfume.id'], ondelete='CASCADE'
        ),

        # 인덱스 설정
        sa.Index('ix_pbti_recommendation_type_code', 'type_code'),
        sa.Index('ix_pbti_recommendation_perfume_id', 'perfume_id')
    )


def downgrade() -> None:
    op.drop_table('pbti_recommendation')