"""Add performance indexes

Revision ID: 002
Revises: 001
Create Date: 2026-02-15 04:51:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes for better query performance"""
    
    # Users table indexes
    op.create_index('ix_users_email_active', 'users', ['email', 'is_active'], unique=False)
    op.create_index('ix_users_created_at', 'users', ['created_at'], unique=False)
    op.create_index('ix_users_last_login', 'users', ['last_login_at'], unique=False)
    
    # Sessions table indexes
    op.create_index('ix_sessions_user_status', 'sessions', ['user_id', 'status'], unique=False)
    op.create_index('ix_sessions_created_at', 'sessions', ['created_at'], unique=False)
    op.create_index('ix_sessions_updated_at', 'sessions', ['updated_at'], unique=False)
    op.create_index('ix_sessions_status_created', 'sessions', ['status', 'created_at'], unique=False)
    
    # Skills table indexes
    op.create_index('ix_skills_user_active', 'skills', ['user_id', 'is_active'], unique=False)
    op.create_index('ix_skills_name_public', 'skills', ['name', 'is_public'], unique=False)
    op.create_index('ix_skills_created_at', 'skills', ['created_at'], unique=False)
    op.create_index('ix_skills_type_public', 'skills', ['skill_type', 'is_public'], unique=False)
    op.create_index('ix_skills_execution_count', 'skills', ['execution_count'], unique=False)
    
    # Skill files table indexes
    op.create_index('ix_skill_files_skill_type', 'skill_files', ['skill_id', 'file_type'], unique=False)
    op.create_index('ix_skill_files_path', 'skill_files', ['file_path'], unique=False)
    
    # Skill executions table indexes
    op.create_index('ix_skill_executions_skill_status', 'skill_executions', ['skill_id', 'status'], unique=False)
    op.create_index('ix_skill_executions_user_status', 'skill_executions', ['user_id', 'status'], unique=False)
    op.create_index('ix_skill_executions_created_at', 'skill_executions', ['created_at'], unique=False)
    op.create_index('ix_skill_executions_status_created', 'skill_executions', ['status', 'created_at'], unique=False)
    op.create_index('ix_skill_executions_started_at', 'skill_executions', ['started_at'], unique=False)
    
    # Skill execution logs table indexes
    op.create_index('ix_skill_execution_logs_execution_level', 'skill_execution_logs', ['execution_id', 'log_level'], unique=False)
    op.create_index('ix_skill_execution_logs_created_at', 'skill_execution_logs', ['created_at'], unique=False)
    
    # Files table indexes (if exists)
    try:
        op.create_index('ix_files_user_created', 'files', ['user_id', 'created_at'], unique=False)
        op.create_index('ix_files_type', 'files', ['file_type'], unique=False)
    except Exception:
        pass  # Table might not exist yet


def downgrade() -> None:
    """Remove performance indexes"""
    
    # Users table
    op.drop_index('ix_users_email_active', table_name='users')
    op.drop_index('ix_users_created_at', table_name='users')
    op.drop_index('ix_users_last_login', table_name='users')
    
    # Sessions table
    op.drop_index('ix_sessions_user_status', table_name='sessions')
    op.drop_index('ix_sessions_created_at', table_name='sessions')
    op.drop_index('ix_sessions_updated_at', table_name='sessions')
    op.drop_index('ix_sessions_status_created', table_name='sessions')
    
    # Skills table
    op.drop_index('ix_skills_user_active', table_name='skills')
    op.drop_index('ix_skills_name_public', table_name='skills')
    op.drop_index('ix_skills_created_at', table_name='skills')
    op.drop_index('ix_skills_type_public', table_name='skills')
    op.drop_index('ix_skills_execution_count', table_name='skills')
    
    # Skill files table
    op.drop_index('ix_skill_files_skill_type', table_name='skill_files')
    op.drop_index('ix_skill_files_path', table_name='skill_files')
    
    # Skill executions table
    op.drop_index('ix_skill_executions_skill_status', table_name='skill_executions')
    op.drop_index('ix_skill_executions_user_status', table_name='skill_executions')
    op.drop_index('ix_skill_executions_created_at', table_name='skill_executions')
    op.drop_index('ix_skill_executions_status_created', table_name='skill_executions')
    op.drop_index('ix_skill_executions_started_at', table_name='skill_executions')
    
    # Skill execution logs table
    op.drop_index('ix_skill_execution_logs_execution_level', table_name='skill_execution_logs')
    op.drop_index('ix_skill_execution_logs_created_at', table_name='skill_execution_logs')
    
    # Files table (if exists)
    try:
        op.drop_index('ix_files_user_created', table_name='files')
        op.drop_index('ix_files_type', table_name='files')
    except Exception:
        pass
