"""
工作流执行模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.database import Base
import uuid


class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TriggerType(str, Enum):
    """触发类型"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"
    API = "api"


class StepStatus(str, Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class WorkflowExecution(Base):
    """工作流执行记录"""
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 触发信息
    trigger_type = Column(String(20), default=TriggerType.MANUAL.value, nullable=False)
    triggered_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # 触发用户
    
    # 执行状态
    status = Column(String(20), default=ExecutionStatus.PENDING.value, nullable=False, index=True)
    
    # 输入/输出数据
    input_data = Column(JSON, nullable=True, default=dict)
    output_data = Column(JSON, nullable=True, default=dict)
    
    # 执行上下文（变量快照）
    context_data = Column(JSON, nullable=True, default=dict)
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    error_node_id = Column(String(50), nullable=True)  # 出错的节点ID
    error_stack = Column(Text, nullable=True)  # 错误堆栈
    
    # 执行统计
    total_steps = Column(Integer, default=0, nullable=False)
    completed_steps = Column(Integer, default=0, nullable=False)
    failed_steps = Column(Integer, default=0, nullable=False)
    
    # 时间信息
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    execution_time = Column(Float, nullable=True)  # 执行时间（秒）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 取消/暂停相关
    cancel_reason = Column(Text, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 关系
    workflow = relationship("Workflow", back_populates="executions", foreign_keys=[workflow_id])
    user = relationship("User", foreign_keys=[user_id])
    trigger_user = relationship("User", foreign_keys=[triggered_by])
    cancel_user = relationship("User", foreign_keys=[cancelled_by])
    steps = relationship("WorkflowExecutionStep", back_populates="execution", cascade="all, delete-orphan")
    logs = relationship("ExecutionLog", back_populates="execution", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, workflow_id={self.workflow_id}, status={self.status})>"


class WorkflowExecutionStep(Base):
    """工作流执行步骤记录"""
    __tablename__ = "workflow_execution_steps"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("workflow_executions.id"), nullable=False, index=True)
    
    # 节点信息
    node_id = Column(String(50), nullable=False, index=True)  # 对应工作流定义中的节点ID
    node_type = Column(String(50), nullable=False)  # start, end, skill, condition, transform, parallel
    node_name = Column(String(100), nullable=True)  # 节点名称（便于查看）
    
    # 步骤状态
    status = Column(String(20), default=StepStatus.PENDING.value, nullable=False, index=True)
    
    # 输入/输出数据
    input_data = Column(JSON, nullable=True, default=dict)
    output_data = Column(JSON, nullable=True, default=dict)
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True)  # 错误类型
    error_stack = Column(Text, nullable=True)  # 错误堆栈
    
    # 重试信息
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=0, nullable=False)
    retry_config = Column(JSON, nullable=True)  # 重试配置
    
    # 执行时间
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    execution_time = Column(Float, nullable=True)  # 执行时间（秒）
    
    # 依赖关系（用于并行执行）
    depends_on = Column(JSON, nullable=True, default=list)  # 依赖的步骤ID列表
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    execution = relationship("WorkflowExecution", back_populates="steps")
    logs = relationship("ExecutionLog", back_populates="step", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<WorkflowExecutionStep(id={self.id}, node_id={self.node_id}, status={self.status})>"


class ExecutionLog(Base):
    """执行日志"""
    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("workflow_executions.id"), nullable=False, index=True)
    step_id = Column(Integer, ForeignKey("workflow_execution_steps.id"), nullable=True, index=True)
    
    # 日志信息
    level = Column(String(20), default="INFO", nullable=False)  # DEBUG, INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    
    # 额外数据
    metadata = Column(JSON, nullable=True, default=dict)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关系
    execution = relationship("WorkflowExecution", back_populates="logs")
    step = relationship("WorkflowExecutionStep", back_populates="logs")
    
    def __repr__(self):
        return f"<ExecutionLog(id={self.id}, level={self.level}, message={self.message[:50]})>"
