"""create skill invocation logs tables

Revision ID: v1.0.0_skill_monitoring
Revises: 
Create Date: 2024-02-15 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'v1.0.0_skill_monitoring'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建技能调用日志表
    op.create_table(
        'skill_invocation_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('skill_name', sa.String(length=255), nullable=False),
        sa.Column('skill_version', sa.String(length=50), nullable=True),
        sa.Column('execution_type', sa.String(length=50), nullable=False, server_default='api'),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('input_params', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('output_data', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=True),
        sa.Column('error_stack_trace', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('memory_bytes', sa.Integer(), nullable=True),
        sa.Column('cpu_percent', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index(op.f('ix_skill_invocation_logs_id'), 'skill_invocation_logs', ['id'], unique=False)
    op.create_index(op.f('ix_skill_invocation_logs_skill_id'), 'skill_invocation_logs', ['skill_id'], unique=False)
    op.create_index(op.f('ix_skill_invocation_logs_status'), 'skill_invocation_logs', ['status'], unique=False)
    op.create_index(op.f('ix_skill_invocation_logs_user_id'), 'skill_invocation_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_skill_invocation_logs_session_id'), 'skill_invocation_logs', ['session_id'], unique=False)
    op.create_index(op.f('ix_skill_invocation_logs_request_id'), 'skill_invocation_logs', ['request_id'], unique=False)
    op.create_index(op.f('ix_skill_invocation_logs_started_at'), 'skill_invocation_logs', ['started_at'], unique=False)
    op.create_index('idx_skill_invocation_skill_date', 'skill_invocation_logs', ['skill_id', 'started_at'], unique=False)
    op.create_index('idx_skill_invocation_user_date', 'skill_invocation_logs', ['user_id', 'started_at'], unique=False)
    op.create_index('idx_skill_invocation_status_date', 'skill_invocation_logs', ['status', 'started_at'], unique=False)
    
    # 创建技能错误日志表
    op.create_table(
        'skill_error_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('skill_name', sa.String(length=255), nullable=False),
        sa.Column('error_type', sa.String(length=100), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('occurrence_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('last_occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('first_occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sample_stack_trace', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index(op.f('ix_skill_error_logs_id'), 'skill_error_logs', ['id'], unique=False)
    op.create_index(op.f('ix_skill_error_logs_skill_id'), 'skill_error_logs', ['skill_id'], unique=False)
    op.create_index(op.f('ix_skill_error_logs_error_type'), 'skill_error_logs', ['error_type'], unique=False)
    op.create_index('idx_skill_error_skill_type', 'skill_error_logs', ['skill_id', 'error_type'], unique=False)
    op.create_index('idx_skill_error_last_occurred', 'skill_error_logs', ['last_occurred_at'], unique=False)


def downgrade() -> None:
    # 删除技能错误日志表
    op.drop_index('idx_skill_error_last_occurred', table_name='skill_error_logs')
    op.drop_index('idx_skill_error_skill_type', table_name='skill_error_logs')
    op.drop_index(op.f('ix_skill_error_logs_error_type'), table_name='skill_error_logs')
    op.drop_index(op.f('ix_skill_error_logs_skill_id'), table_name='skill_error_logs')
    op.drop_index(op.f('ix_skill_error_logs_id'), table_name='skill_error_logs')
    op.drop_table('skill_error_logs')
    
    # 删除技能调用日志表
    op.drop_index('idx_skill_invocation_status_date', table_name='skill_invocation_logs')
    op.drop_index('idx_skill_invocation_user_date', table_name='skill_invocation_logs')
    op.drop_index('idx_skill_invocation_skill_date', table_name='skill_invocation_logs')
    op.drop_index(op.f('ix_skill_invocation_logs_started_at'), table_name='skill_invocation_logs')
    op.drop_index(op.f('ix_skill_invocation_logs_request_id'), table_name='skill_invocation_logs')
    op.drop_index(op.f('ix_skill_invocation_logs_session_id'), table_name='skill_invocation_logs')
    op.drop_index(op.f('ix_skill_invocation_logs_user_id'), table_name='skill_invocation_logs')
    op.drop_index(op.f('ix_skill_invocation_logs_status'), table_name='skill_invocation_logs')
    op.drop_index(op.f('ix_skill_invocation_logs_skill_id'), table_name='skill_invocation_logs')
    op.drop_index(op.f('ix_skill_invocation_logs_id'), table_name='skill_invocation_logs')
    op.drop_table('skill_invocation_logs')
