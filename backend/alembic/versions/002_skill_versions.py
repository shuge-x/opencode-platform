"""add skill_versions table

Revision ID: 002_skill_versions
Revises: 001_initial_schema
Create Date: 2024-02-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_skill_versions'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # 创建 skill_versions 表
    op.create_table(
        'skill_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('version_name', sa.String(length=100), nullable=True),
        sa.Column('commit_hash', sa.String(length=40), nullable=False),
        sa.Column('commit_message', sa.Text(), nullable=True),
        sa.Column('is_release', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_latest', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('files_changed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('additions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('deletions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_skill_versions_id'), 'skill_versions', ['id'], unique=False)
    op.create_index(op.f('ix_skill_versions_skill_id'), 'skill_versions', ['skill_id'], unique=False)
    op.create_index(op.f('ix_skill_versions_user_id'), 'skill_versions', ['user_id'], unique=False)
    op.create_index(op.f('ix_skill_versions_commit_hash'), 'skill_versions', ['commit_hash'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_skill_versions_commit_hash'), table_name='skill_versions')
    op.drop_index(op.f('ix_skill_versions_user_id'), table_name='skill_versions')
    op.drop_index(op.f('ix_skill_versions_skill_id'), table_name='skill_versions')
    op.drop_index(op.f('ix_skill_versions_id'), table_name='skill_versions')
    op.drop_table('skill_versions')
