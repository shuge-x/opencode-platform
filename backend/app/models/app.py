"""
应用数据模型
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class App(Base):
    """
    应用模型
    
    存储用户创建的应用
    """
    __tablename__ = "apps"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 关联用户
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 应用信息
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    icon: Mapped[Optional[str]] = mapped_column(String(500))
    
    # 应用配置
    app_type: Mapped[str] = mapped_column(
        String(50),
        default="chat",
        comment="应用类型: chat, workflow, agent"
    )
    config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict,
        comment="应用配置"
    )
    
    # API密钥
    api_key: Mapped[Optional[str]] = mapped_column(
        String(100),
        unique=True,
        index=True,
        comment="应用API密钥"
    )
    
    # 状态
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否公开"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活"
    )
    
    # 统计
    use_count: Mapped[int] = mapped_column(
        default=0,
        comment="使用次数"
    )
    install_count: Mapped[int] = mapped_column(
        default=0,
        comment="安装次数"
    )
    
    # 元数据
    tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
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
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # 关系
    user = relationship("User", back_populates="apps")
    
    def __repr__(self) -> str:
        return f"<App(id={self.id}, name={self.name}, type={self.app_type})>"
