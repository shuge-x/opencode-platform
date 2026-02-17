"""add workflow execution indexes

Revision ID: 005_add_workflow_execution_indexes
Revises: 004_add_workflow_tables
Create Date: 2026-02-17 07:15:00

优化工作流执行性能的索引
- 支持 100+ 节点工作流的快速查询
- 优化执行历史查询
- 加速步骤状态检索
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_workflow_execution_indexes'
down_revision = '004_add_workflow_tables'
branch_labels = None
depends_on = None


def upgrade():
    """添加工作流执行相关索引"""
    
    # ============ workflow_executions 表索引 ============
    
    # 复合索引：按工作流ID和状态查询执行记录（最常用查询）
    op.create_index(
        'idx_workflow_executions_workflow_status',
        'workflow_executions',
        ['workflow_id', 'status'],
        postgresql_where=sa.text("status IN ('pending', 'running', 'completed', 'failed')")
    )
    
    # 复合索引：按用户ID和创建时间查询执行历史（用户执行历史页面）
    op.create_index(
        'idx_workflow_executions_user_created',
        'workflow_executions',
        ['user_id', 'created_at DESC']
    )
    
    # 复合索引：按工作流ID和时间范围查询（统计分析）
    op.create_index(
        'idx_workflow_executions_workflow_time',
        'workflow_executions',
        ['workflow_id', 'started_at', 'finished_at']
    )
    
    # 触发类型索引（按触发方式统计）
    op.create_index(
        'idx_workflow_executions_trigger',
        'workflow_executions',
        ['trigger_type', 'created_at DESC']
    )
    
    # 执行时间索引（性能监控和慢查询分析）
    op.create_index(
        'idx_workflow_executions_performance',
        'workflow_executions',
        ['execution_time'],
        postgresql_where=sa.text("execution_time IS NOT NULL AND execution_time > 5.0")
    )
    
    # 失败执行索引（快速定位失败任务）
    op.create_index(
        'idx_workflow_executions_failures',
        'workflow_executions',
        ['status', 'created_at DESC'],
        postgresql_where=sa.text("status = 'failed'")
    )
    
    # ============ workflow_execution_steps 表索引 ============
    
    # 复合索引：按执行ID和状态查询步骤（执行详情页面）
    op.create_index(
        'idx_workflow_steps_execution_status',
        'workflow_execution_steps',
        ['execution_id', 'status']
    )
    
    # 节点类型索引（按节点类型统计性能）
    op.create_index(
        'idx_workflow_steps_node_type',
        'workflow_execution_steps',
        ['node_type', 'execution_time'],
        postgresql_where=sa.text("execution_time IS NOT NULL")
    )
    
    # 重试步骤索引（分析重试模式）
    op.create_index(
        'idx_workflow_steps_retries',
        'workflow_execution_steps',
        ['retry_count', 'status'],
        postgresql_where=sa.text("retry_count > 0")
    )
    
    # 时间范围索引（步骤执行时间分析）
    op.create_index(
        'idx_workflow_steps_time_range',
        'workflow_execution_steps',
        ['started_at', 'finished_at']
    )
    
    # ============ execution_logs 表索引 ============
    
    # 复合索引：按执行ID和日志级别查询（日志查看页面）
    op.create_index(
        'idx_execution_logs_execution_level',
        'execution_logs',
        ['execution_id', 'level', 'created_at DESC']
    )
    
    # 步骤日志索引（按步骤查看日志）
    op.create_index(
        'idx_execution_logs_step',
        'execution_logs',
        ['step_id', 'created_at DESC'],
        postgresql_where=sa.text("step_id IS NOT NULL")
    )
    
    # 错误日志快速查询索引
    op.create_index(
        'idx_execution_logs_errors',
        'execution_logs',
        ['level', 'created_at DESC'],
        postgresql_where=sa.text("level IN ('ERROR', 'WARNING')")
    )
    
    # 时间范围索引（日志时间范围查询）
    op.create_index(
        'idx_execution_logs_time_range',
        'execution_logs',
        ['created_at']
    )


def downgrade():
    """移除工作流执行相关索引"""
    
    # 移除 workflow_executions 索引
    op.drop_index('idx_workflow_executions_performance', 'workflow_executions')
    op.drop_index('idx_workflow_executions_failures', 'workflow_executions')
    op.drop_index('idx_workflow_executions_trigger', 'workflow_executions')
    op.drop_index('idx_workflow_executions_workflow_time', 'workflow_executions')
    op.drop_index('idx_workflow_executions_user_created', 'workflow_executions')
    op.drop_index('idx_workflow_executions_workflow_status', 'workflow_executions')
    
    # 移除 workflow_execution_steps 索引
    op.drop_index('idx_workflow_steps_time_range', 'workflow_execution_steps')
    op.drop_index('idx_workflow_steps_retries', 'workflow_execution_steps')
    op.drop_index('idx_workflow_steps_node_type', 'workflow_execution_steps')
    op.drop_index('idx_workflow_steps_execution_status', 'workflow_execution_steps')
    
    # 移除 execution_logs 索引
    op.drop_index('idx_execution_logs_time_range', 'execution_logs')
    op.drop_index('idx_execution_logs_errors', 'execution_logs')
    op.drop_index('idx_execution_logs_step', 'execution_logs')
    op.drop_index('idx_execution_logs_execution_level', 'execution_logs')
