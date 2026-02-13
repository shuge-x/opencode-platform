"""
文件数据模型
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, BigInteger, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class File(Base):
    """
    文件模型
    
    存储用户上传的文件信息
    """
    __tablename__ = "files"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 关联用户
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 文件信息
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="原始文件名"
    )
    stored_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="存储文件名（UUID）"
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="文件存储路径"
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="文件大小（字节）"
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="MIME类型"
    )
    
    # 元数据
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="文件描述"
    )
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict,
        comment="文件元数据"
    )
    
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
    user = relationship("User", back_populates="files")
    
    def __repr__(self) -> str:
        return f"<File(id={self.id}, filename={self.filename}, size={self.file_size})>"
