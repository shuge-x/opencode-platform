"""
工作流数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Workflow(Base):
    """工作流"""
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    definition = Column(JSON, nullable=False)  # {nodes: [], edges: []}
    variables = Column(JSON, nullable=True)  # 输入变量定义
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    user = relationship("User", backref="workflows")

    def __repr__(self):
        return f"<Workflow(id={self.id}, name={self.name}, user_id={self.user_id})>"
