"""
技能数据模型
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Skill(Base):
    """
    技能模型
    
    存储用户自定义技能
    """
    __tablename__ = "skills"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 关联用户
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 技能信息
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    
    # 技能内容
    prompt_template: Mapped[str] = mapped_column(
        Text,
        comment="技能提示词模板"
    )
    config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict,
        comment="技能配置"
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
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否经过平台验证"
    )
    
    # 统计
    use_count: Mapped[int] = mapped_column(
        default=0,
        comment="使用次数"
    )
    like_count: Mapped[int] = mapped_column(
        default=0,
        comment="点赞数"
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
    
    # 关系
    user = relationship("User", back_populates="skills")
    
    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name={self.name}, slug={self.slug})>"
