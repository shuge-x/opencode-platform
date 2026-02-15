"""
技能分类模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class SkillCategory(Base):
    """技能分类"""
    __tablename__ = "skill_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    slug = Column(String(60), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("skill_categories.id"), nullable=True)
    icon = Column(String(50), nullable=True)  # 图标名称
    color = Column(String(20), nullable=True)  # 分类颜色

    # 排序和状态
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # 统计
    skill_count = Column(Integer, default=0, nullable=False)  # 技能数量缓存

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    children = relationship("SkillCategory", backref="parent", remote_side=[id])

    def __repr__(self):
        return f"<SkillCategory(id={self.id}, name={self.name}, slug={self.slug})>"


class SkillCategoryMapping(Base):
    """技能-分类关联（一个技能可以属于多个分类）"""
    __tablename__ = "skill_category_mappings"

    id = Column(Integer, primary_key=True, index=True)
    published_skill_id = Column(Integer, ForeignKey("published_skills.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("skill_categories.id", ondelete="CASCADE"), nullable=False, index=True)
    is_primary = Column(Boolean, default=False, nullable=False)  # 是否为主分类

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SkillCategoryMapping(skill_id={self.published_skill_id}, category_id={self.category_id})>"
