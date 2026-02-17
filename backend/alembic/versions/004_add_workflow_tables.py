"""add workflow tables

Revision ID: 004_workflow
Revises: v1.0.0_skill_monitoring
Create Date: 2026-02-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_workflow'
down_revision: Union[str, None] = 'v1.0.0_skill_monitoring'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建 workflows 表
    op.create_table(
        'workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('definition', sa.JSON, nullable=False),
        sa.Column('variables', sa.JSON, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.utcnow(), nullable=False),
        sa.Column('updated_at', sa.DateTime, default=sa.func.utcnow(), onupdate=sa.func.utcnow(), nullable=False),
    )
    
    # 创建索引
    op.create_index('ix_workflows_user_id', 'workflows', ['user_id'])
    op.create_index('ix_workflows_is_active', 'workflows', ['is_active'])
    op.create_index('ix_workflows_created_at', 'workflows', ['created_at'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('ix_workflows_created_at', table_name='workflows')
    op.drop_index('ix_workflows_is_active', table_name='workflows')
    op.drop_index('ix_workflows_user_id', table_name='workflows')
    
    # 删除表
    op.drop_table('workflows')
