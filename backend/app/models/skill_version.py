"""
技能版本数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class SkillVersion(Base):
    """技能版本"""
    __tablename__ = "skill_versions"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 版本信息
    version_name = Column(String(100), nullable=True)  # 可选的版本名称（如 v1.0.0）
    commit_hash = Column(String(40), nullable=False, index=True)  # Git commit hash
    commit_message = Column(Text, nullable=True)  # 提交信息
    
    # 版本标签
    is_release = Column(Boolean, default=False, nullable=False)  # 是否为正式发布版本
    is_latest = Column(Boolean, default=False, nullable=False)  # 是否为最新版本
    
    # 变更统计
    files_changed = Column(Integer, default=0, nullable=False)
    additions = Column(Integer, default=0, nullable=False)
    deletions = Column(Integer, default=0, nullable=False)
    
    # 元数据
    metadata = Column(JSON, nullable=True)  # 额外元数据
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    skill = relationship("Skill", backref="versions")
    user = relationship("User", backref="skill_versions")

    def __repr__(self):
        return f"<SkillVersion(id={self.id}, skill_id={self.skill_id}, commit={self.commit_hash[:7]})>"
