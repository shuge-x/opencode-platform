"""
会话相关的Pydantic schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SessionConfig(BaseModel):
    """会话配置模型"""
    model_name: str = Field(default="gpt-4", description="模型名称")
    temperature: float = Field(default=0.7, ge=0, le=2, description="温度参数")
    max_tokens: int = Field(default=2000, ge=1, le=8000, description="最大token数")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model_name": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000
            }
        }
    )


class SessionBase(BaseModel):
    """会话基础模型"""
    title: Optional[str] = Field(None, max_length=255, description="会话标题")
    description: Optional[str] = Field(None, description="会话描述")
    config: Optional[SessionConfig] = Field(default=None, description="会话配置")


class SessionCreate(SessionBase):
    """会话创建模型"""
    context: Optional[Dict[str, Any]] = Field(default=None, description="初始上下文")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Python开发助手",
                "description": "帮助编写Python代码",
                "config": {
                    "model_name": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            }
        }
    )


class SessionUpdate(BaseModel):
    """会话更新模型"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(created|running|paused|completed|error)$")
    context: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "更新后的标题",
                "status": "running"
            }
        }
    )


class SessionMessage(BaseModel):
    """会话消息模型"""
    role: str = Field(..., pattern="^(user|assistant|system)$", description="消息角色")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[datetime] = Field(default=None, description="时间戳")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "user",
                "content": "如何写一个快速排序？",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
    )


class SessionResponse(SessionBase):
    """会话响应模型"""
    id: int
    user_id: int
    status: str
    config: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    messages: Optional[List[Dict[str, Any]]] = []
    total_messages: int = 0
    total_tokens: int = 0
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    """会话列表响应"""
    items: List[SessionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 10,
                "page": 1,
                "page_size": 20,
                "has_more": False
            }
        }
    )
