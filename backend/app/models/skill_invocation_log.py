"""
技能调用日志模型

存储技能调用的详细日志到 PostgreSQL
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Index
from sqlalchemy.sql import func
from app.database import Base


class SkillInvocationLog(Base):
    """技能调用日志表"""
    __tablename__ = "skill_invocation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 技能信息
    skill_id = Column(Integer, nullable=False, index=True)
    skill_name = Column(String(255), nullable=False)
    skill_version = Column(String(50), nullable=True)
    
    # 执行信息
    execution_type = Column(String(50), nullable=False, default="api")  # api/websocket/scheduled
    status = Column(String(20), nullable=False, index=True)  # success/error/timeout
    
    # 用户信息
    user_id = Column(Integer, nullable=True, index=True)
    session_id = Column(Integer, nullable=True, index=True)
    
    # 请求信息
    request_id = Column(String(100), nullable=True, index=True)
    input_params = Column(JSON, nullable=True)
    
    # 响应信息
    output_data = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True)
    error_stack_trace = Column(Text, nullable=True)
    
    # 性能指标
    duration_ms = Column(Integer, nullable=True)
    memory_bytes = Column(Integer, nullable=True)
    cpu_percent = Column(Float, nullable=True)
    
    # 元数据
    metadata = Column(JSON, nullable=True)
    
    # 时间戳
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 索引
    __table_args__ = (
        Index('idx_skill_invocation_skill_date', 'skill_id', 'started_at'),
        Index('idx_skill_invocation_user_date', 'user_id', 'started_at'),
        Index('idx_skill_invocation_status_date', 'status', 'started_at'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "skill_version": self.skill_version,
            "execution_type": self.execution_type,
            "status": self.status,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "input_params": self.input_params,
            "output_data": self.output_data[:500] if self.output_data else None,  # 截断输出
            "error_message": self.error_message,
            "error_type": self.error_type,
            "duration_ms": self.duration_ms,
            "memory_bytes": self.memory_bytes,
            "cpu_percent": self.cpu_percent,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class SkillErrorLog(Base):
    """技能错误日志表 - 聚合错误"""
    __tablename__ = "skill_error_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 错误信息
    skill_id = Column(Integer, nullable=False, index=True)
    skill_name = Column(String(255), nullable=False)
    error_type = Column(String(100), nullable=False, index=True)
    error_message = Column(Text, nullable=False)
    
    # 聚合统计
    occurrence_count = Column(Integer, nullable=False, default=1)
    last_occurred_at = Column(DateTime(timezone=True), nullable=False)
    first_occurred_at = Column(DateTime(timezone=True), nullable=False)
    
    # 示例堆栈
    sample_stack_trace = Column(Text, nullable=True)
    
    # 元数据
    metadata = Column(JSON, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 索引
    __table_args__ = (
        Index('idx_skill_error_skill_type', 'skill_id', 'error_type'),
        Index('idx_skill_error_last_occurred', 'last_occurred_at'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "error_type": self.error_type,
            "error_message": self.error_message[:200] if self.error_message else None,
            "occurrence_count": self.occurrence_count,
            "last_occurred_at": self.last_occurred_at.isoformat() if self.last_occurred_at else None,
            "first_occurred_at": self.first_occurred_at.isoformat() if self.first_occurred_at else None,
        }
