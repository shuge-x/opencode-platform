"""
已发布技能数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class PublishedSkill(Base):
    """已发布技能"""
    __tablename__ = "published_skills"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False, index=True)
    publisher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 基本信息
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(120), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    version = Column(String(20), default="1.0.0", nullable=False)

    # 分类和标签
    category = Column(String(50), nullable=True, index=True)
    tags = Column(JSON, nullable=True)  # 标签列表

    # 定价信息
    price = Column(Numeric(10, 2), default=0.00, nullable=False)  # 价格（0表示免费）
    currency = Column(String(10), default="USD", nullable=False)

    # 发布状态
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, published, rejected, deprecated
    is_public = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)  # 是否精选

    # 统计信息
    download_count = Column(Integer, default=0, nullable=False)
    install_count = Column(Integer, default=0, nullable=False)
    rating = Column(Numeric(3, 2), default=0.00, nullable=False)  # 平均评分 0-5
    rating_count = Column(Integer, default=0, nullable=False)

    # 元数据
    homepage_url = Column(String(500), nullable=True)
    repository_url = Column(String(500), nullable=True)
    documentation_url = Column(String(500), nullable=True)
    license = Column(String(50), default="MIT", nullable=False)

    # 时间戳
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    publisher = relationship("User", backref="published_skills")
    packages = relationship("SkillPackage", back_populates="published_skill", cascade="all, delete-orphan")
    permissions = relationship("SkillPermission", back_populates="published_skill", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PublishedSkill(id={self.id}, name={self.name}, version={self.version})>"


class SkillPackage(Base):
    """技能包"""
    __tablename__ = "skill_packages"

    id = Column(Integer, primary_key=True, index=True)
    published_skill_id = Column(Integer, ForeignKey("published_skills.id"), nullable=False, index=True)

    # 版本信息
    version = Column(String(20), nullable=False, index=True)
    version_code = Column(Integer, default=1, nullable=False)  # 版本号数字形式，用于比较

    # 存储信息
    storage_path = Column(String(500), nullable=False)  # MinIO中的对象路径
    file_size = Column(Integer, nullable=False)  # 文件大小（字节）
    checksum = Column(String(64), nullable=False)  # SHA256校验和

    # 依赖信息
    dependencies = Column(JSON, nullable=True)  # 依赖列表
    min_platform_version = Column(String(20), nullable=True)  # 最低平台版本要求

    # 发布说明
    release_notes = Column(Text, nullable=True)
    changelog = Column(Text, nullable=True)

    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    is_latest = Column(Boolean, default=False, nullable=False)  # 是否最新版本

    # 统计
    download_count = Column(Integer, default=0, nullable=False)

    # 时间戳
    published_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    published_skill = relationship("PublishedSkill", back_populates="packages")

    def __repr__(self):
        return f"<SkillPackage(id={self.id}, version={self.version}, skill_id={self.published_skill_id})>"


class SkillPermission(Base):
    """技能权限"""
    __tablename__ = "skill_permissions"

    id = Column(Integer, primary_key=True, index=True)
    published_skill_id = Column(Integer, ForeignKey("published_skills.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 权限类型
    permission_type = Column(String(20), nullable=False)  # owner, admin, write, read
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 时间戳
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # 过期时间（可选）

    # 关系
    published_skill = relationship("PublishedSkill", back_populates="permissions")

    def __repr__(self):
        return f"<SkillPermission(skill_id={self.published_skill_id}, user_id={self.user_id}, type={self.permission_type})>"


class SkillReview(Base):
    """技能评价"""
    __tablename__ = "skill_reviews"

    id = Column(Integer, primary_key=True, index=True)
    published_skill_id = Column(Integer, ForeignKey("published_skills.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 评价内容
    rating = Column(Integer, nullable=False)  # 1-5星
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=True)

    # 审核状态
    status = Column(String(20), default="approved", nullable=False)  # pending, approved, rejected
    is_edited = Column(Boolean, default=False, nullable=False)  # 是否编辑过

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SkillReview(skill_id={self.published_skill_id}, user_id={self.user_id}, rating={self.rating})>"


class SkillRating(Base):
    """技能评分（独立于评论）"""
    __tablename__ = "skill_ratings"
    __table_args__ = (
        UniqueConstraint('published_skill_id', 'user_id', name='uq_skill_rating_user'),
    )

    id = Column(Integer, primary_key=True, index=True)
    published_skill_id = Column(Integer, ForeignKey("published_skills.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 评分
    rating = Column(Integer, nullable=False)  # 1-5星

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SkillRating(skill_id={self.published_skill_id}, user_id={self.user_id}, rating={self.rating})>"


class SkillBookmark(Base):
    """技能收藏"""
    __tablename__ = "skill_bookmarks"
    __table_args__ = (
        UniqueConstraint('published_skill_id', 'user_id', name='uq_skill_bookmark_user'),
    )

    id = Column(Integer, primary_key=True, index=True)
    published_skill_id = Column(Integer, ForeignKey("published_skills.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 收藏信息
    notes = Column(Text, nullable=True)  # 用户备注

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SkillBookmark(skill_id={self.published_skill_id}, user_id={self.user_id})>"
