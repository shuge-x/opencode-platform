"""
会话数据模型
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Session(Base):
    """
    会话模型
    
    存储OpenCode会话信息
    """
    __tablename__ = "sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 关联用户
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 会话信息
    title: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # 会话状态
    status: Mapped[str] = mapped_column(
        String(50),
        default="created",
        comment="created, running, paused, completed, error"
    )
    
    # 会话配置
    model_name: Mapped[str] = mapped_column(
        String(100),
        default="gpt-4",
        comment="使用的模型名称"
    )
    temperature: Mapped[float] = mapped_column(default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2000)
    
    # 会话上下文
    context: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict,
        comment="会话上下文信息"
    )
    messages: Mapped[Optional[list]] = mapped_column(
        JSON,
        default=list,
        comment="消息历史"
    )
    
    # 统计信息
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    
    # 元数据
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # 关系
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, title={self.title}, status={self.status})>"
