"""Add gateway tables

Revision ID: 003_gateway_tables
Revises: 002_add_performance_indexes
Create Date: 2026-02-15 12:53:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_gateway_tables'
down_revision: Union[str, None] = '002_add_performance_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建gateway_routes表
    op.create_table(
        'gateway_routes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('service_name', sa.String(length=100), nullable=False),
        sa.Column('service_url', sa.String(length=500), nullable=False),
        sa.Column('methods', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('rate_limit', sa.Integer(), nullable=True),
        sa.Column('rate_limit_window', sa.Integer(), nullable=True),
        sa.Column('require_auth', sa.Boolean(), nullable=True),
        sa.Column('require_api_key', sa.Boolean(), nullable=True),
        sa.Column('cors_enabled', sa.Boolean(), nullable=True),
        sa.Column('timeout_ms', sa.Integer(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_id', sa.String(length=100), nullable=True),
        sa.Column('sync_status', sa.String(length=20), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('sync_error', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index(op.f('ix_gateway_routes_name'), 'gateway_routes', ['name'], unique=True)
    op.create_index(op.f('ix_gateway_routes_external_id'), 'gateway_routes', ['external_id'], unique=False)
    
    # 创建api_keys表
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('key_prefix', sa.String(length=8), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scopes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('allowed_routes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('allowed_ips', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('rate_limit', sa.Integer(), nullable=True),
        sa.Column('daily_limit', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('total_requests', sa.Integer(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index(op.f('ix_api_keys_key_hash'), 'api_keys', ['key_hash'], unique=True)
    op.create_index(op.f('ix_api_keys_key_prefix'), 'api_keys', ['key_prefix'], unique=False)
    op.create_index(op.f('ix_api_keys_user_id'), 'api_keys', ['user_id'], unique=False)
    
    # 创建rate_limit_logs表
    op.create_table(
        'rate_limit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('key_type', sa.String(length=20), nullable=False),
        sa.Column('key_value', sa.String(length=100), nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=True),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('limit', sa.Integer(), nullable=False),
        sa.Column('window_seconds', sa.Integer(), nullable=False),
        sa.Column('current_count', sa.Integer(), nullable=False),
        sa.Column('blocked', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['route_id'], ['gateway_routes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index(op.f('ix_rate_limit_logs_key_value'), 'rate_limit_logs', ['key_value'], unique=False)
    op.create_index(op.f('ix_rate_limit_logs_created_at'), 'rate_limit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_rate_limit_logs_created_at'), table_name='rate_limit_logs')
    op.drop_index(op.f('ix_rate_limit_logs_key_value'), table_name='rate_limit_logs')
    op.drop_table('rate_limit_logs')
    
    op.drop_index(op.f('ix_api_keys_user_id'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_key_prefix'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_key_hash'), table_name='api_keys')
    op.drop_table('api_keys')
    
    op.drop_index(op.f('ix_gateway_routes_external_id'), table_name='gateway_routes')
    op.drop_index(op.f('ix_gateway_routes_name'), table_name='gateway_routes')
    op.drop_table('gateway_routes')
