"""
工具调用 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ToolStatus(str, Enum):
    """工具调用状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PERMISSION_REQUIRED = "permission_required"
    PERMISSION_DENIED = "permission_denied"


class ToolCallCreate(BaseModel):
    """创建工具调用"""
    session_id: int
    message_id: Optional[int] = None
    tool_name: str
    tool_description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    requires_permission: bool = False
    permission_reason: Optional[str] = None


class ToolExecutionLogCreate(BaseModel):
    """创建工具执行日志"""
    tool_call_id: int
    log_level: str = "INFO"
    message: str
    metadata: Optional[Dict[str, Any]] = None


class ToolExecutionLogResponse(BaseModel):
    """工具执行日志响应"""
    id: int
    tool_call_id: int
    log_level: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ToolCallResponse(BaseModel):
    """工具调用响应"""
    id: int
    session_id: int
    message_id: Optional[int] = None
    tool_name: str
    tool_description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    status: ToolStatus
    result: Optional[str] = None
    error_message: Optional[str] = None
    requires_permission: bool
    permission_granted: Optional[bool] = None
    permission_reason: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    execution_logs: List[ToolExecutionLogResponse] = []
    
    class Config:
        from_attributes = True


class ToolCallListResponse(BaseModel):
    """工具调用列表响应"""
    items: List[ToolCallResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class PermissionDecision(BaseModel):
    """权限确认决策"""
    granted: bool
    reason: Optional[str] = None
