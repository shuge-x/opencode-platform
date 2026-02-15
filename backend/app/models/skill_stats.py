"""
技能统计数据模型

记录技能的各种统计数据：
- 下载量统计（按日期/版本）
- 使用量统计（调用次数）
- 评分统计（分布、趋势）
- 访问量统计（浏览次数）
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Numeric, Date, Index
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.database import Base


class SkillDailyStats(Base):
    """技能每日统计"""
    __tablename__ = "skill_daily_stats"
    __table_args__ = (
        Index('ix_skill_daily_stats_skill_date', 'skill_id', 'stat_date', unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("published_skills.id"), nullable=False, index=True)
    stat_date = Column(Date, nullable=False, index=True)

    # 下载统计
    download_count = Column(Integer, default=0, nullable=False)
    unique_downloads = Column(Integer, default=0, nullable=False)  # 唯一下载用户数

    # 安装统计
    install_count = Column(Integer, default=0, nullable=False)
    unique_installs = Column(Integer, default=0, nullable=False)  # 唯一安装用户数

    # 使用统计
    execution_count = Column(Integer, default=0, nullable=False)  # 执行/调用次数
    unique_executions = Column(Integer, default=0, nullable=False)  # 唯一执行用户数

    # 访问统计
    view_count = Column(Integer, default=0, nullable=False)  # 浏览次数
    unique_views = Column(Integer, default=0, nullable=False)  # 唯一浏览用户数

    # 评价统计
    new_ratings = Column(Integer, default=0, nullable=False)  # 新增评价数
    new_reviews = Column(Integer, default=0, nullable=False)  # 新增评论数

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    skill = relationship("PublishedSkill", backref="daily_stats")

    def __repr__(self):
        return f"<SkillDailyStats(skill_id={self.skill_id}, date={self.stat_date})>"


class SkillVersionStats(Base):
    """技能版本统计"""
    __tablename__ = "skill_version_stats"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("skill_packages.id"), nullable=False, index=True)
    
    # 下载统计
    download_count = Column(Integer, default=0, nullable=False)
    unique_downloads = Column(Integer, default=0, nullable=False)

    # 安装统计
    install_count = Column(Integer, default=0, nullable=False)
    active_installs = Column(Integer, default=0, nullable=False)  # 当前活跃安装数

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    package = relationship("SkillPackage", backref="version_stats")

    def __repr__(self):
        return f"<SkillVersionStats(package_id={self.package_id})>"


class SkillRatingDistribution(Base):
    """技能评分分布"""
    __tablename__ = "skill_rating_distribution"
    __table_args__ = (
        Index('ix_skill_rating_dist_skill_date', 'skill_id', 'stat_date', unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("published_skills.id"), nullable=False, index=True)
    stat_date = Column(Date, nullable=False, index=True)

    # 评分分布 (1-5星各多少个)
    rating_1_count = Column(Integer, default=0, nullable=False)
    rating_2_count = Column(Integer, default=0, nullable=False)
    rating_3_count = Column(Integer, default=0, nullable=False)
    rating_4_count = Column(Integer, default=0, nullable=False)
    rating_5_count = Column(Integer, default=0, nullable=False)

    # 计算字段
    total_ratings = Column(Integer, default=0, nullable=False)
    avg_rating = Column(Numeric(3, 2), default=0.00, nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    skill = relationship("PublishedSkill", backref="rating_distributions")

    def __repr__(self):
        return f"<SkillRatingDistribution(skill_id={self.skill_id}, date={self.stat_date})>"


class SkillExecutionLog(Base):
    """技能执行日志（用于统计）"""
    __tablename__ = "skill_execution_logs"
    __table_args__ = (
        Index('ix_skill_exec_logs_skill_created', 'skill_id', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("published_skills.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True, index=True)
    package_id = Column(Integer, ForeignKey("skill_packages.id"), nullable=True)

    # 执行信息
    execution_type = Column(String(50), default="invoke", nullable=False)  # invoke, test, preview
    version = Column(String(20), nullable=True)  # 使用的版本

    # 执行结果
    status = Column(String(20), default="success", nullable=False)  # success, error, timeout
    duration_ms = Column(Integer, nullable=True)  # 执行时长（毫秒）
    error_message = Column(Text, nullable=True)

    # 元数据
    metadata = Column(JSON, nullable=True)  # 其他元数据

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 关系
    skill = relationship("PublishedSkill", backref="execution_logs")

    def __repr__(self):
        return f"<SkillExecutionLog(skill_id={self.skill_id}, status={self.status})>"


class SkillViewLog(Base):
    """技能浏览日志"""
    __tablename__ = "skill_view_logs"
    __table_args__ = (
        Index('ix_skill_view_logs_skill_created', 'skill_id', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("published_skills.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # 浏览来源
    source = Column(String(50), nullable=True)  # search, category, recommendation, direct
    referrer = Column(String(500), nullable=True)  # 来源URL

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 关系
    skill = relationship("PublishedSkill", backref="view_logs")

    def __repr__(self):
        return f"<SkillViewLog(skill_id={self.skill_id})>"


class SkillSearchLog(Base):
    """技能搜索日志"""
    __tablename__ = "skill_search_logs"
    __table_args__ = (
        Index('ix_skill_search_logs_query_created', 'query', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # 搜索信息
    query = Column(String(500), nullable=False, index=True)
    filters = Column(JSON, nullable=True)  # 筛选条件

    # 搜索结果
    result_count = Column(Integer, default=0, nullable=False)
    clicked_skill_id = Column(Integer, ForeignKey("published_skills.id"), nullable=True)  # 用户点击的技能

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<SkillSearchLog(query={self.query[:30]}...)>"
