"""
工具调用数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class ToolStatus(str, enum.Enum):
    """工具调用状态"""
    PENDING = "pending"          # 等待执行
    RUNNING = "running"          # 执行中
    SUCCESS = "success"          # 成功
    FAILED = "failed"            # 失败
    PERMISSION_REQUIRED = "permission_required"  # 需要权限确认
    PERMISSION_DENIED = "permission_denied"      # 权限被拒绝


class ToolCall(Base):
    """工具调用记录"""
    __tablename__ = "tool_calls"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True, index=True)
    
    # 工具信息
    tool_name = Column(String(100), nullable=False, index=True)
    tool_description = Column(Text, nullable=True)
    parameters = Column(Text, nullable=True)  # JSON格式的参数
    
    # 执行信息
    status = Column(SQLEnum(ToolStatus), default=ToolStatus.PENDING, nullable=False, index=True)
    result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # 权限相关
    requires_permission = Column(Boolean, default=False)
    permission_granted = Column(Boolean, nullable=True)
    permission_reason = Column(Text, nullable=True)
    
    # 时间戳
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    session = relationship("Session", back_populates="tool_calls")
    message = relationship("Message", back_populates="tool_calls")
    execution_logs = relationship("ToolExecutionLog", back_populates="tool_call", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ToolCall(id={self.id}, tool={self.tool_name}, status={self.status})>"


class ToolExecutionLog(Base):
    """工具执行日志"""
    __tablename__ = "tool_execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    tool_call_id = Column(Integer, ForeignKey("tool_calls.id"), nullable=False, index=True)
    
    # 日志信息
    log_level = Column(String(20), default="INFO", nullable=False)  # DEBUG, INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    metadata = Column(Text, nullable=True)  # JSON格式的额外数据
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    tool_call = relationship("ToolCall", back_populates="execution_logs")
    
    def __repr__(self):
        return f"<ToolExecutionLog(id={self.id}, tool_call_id={self.tool_call_id}, level={self.log_level})>"
