"""
技能数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Skill(Base):
    """技能"""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 基本信息
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    version = Column(String(20), default="1.0.0", nullable=False)

    # 技能类型
    skill_type = Column(String(50), default="custom", nullable=False)  # custom, template, imported

    # 技能配置
    config = Column(JSON, nullable=True)  # 技能配置（JSON格式）
    tags = Column(JSON, nullable=True)  # 标签列表

    # Git 仓库信息
    git_repo_url = Column(String(500), nullable=True)
    git_branch = Column(String(100), default="main", nullable=False)
    git_commit_hash = Column(String(40), nullable=True)

    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)

    # 统计信息
    execution_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    user = relationship("User", back_populates="skills")
    files = relationship("SkillFile", back_populates="skill", cascade="all, delete-orphan")
    executions = relationship("SkillExecution", back_populates="skill", cascade="all, delete-orphan")
    usage_records = relationship("BillingUsage", back_populates="skill")

    def __repr__(self):
        return f"<Skill(id={self.id}, name={self.name}, version={self.version})>"


class SkillFile(Base):
    """技能文件"""
    __tablename__ = "skill_files"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False, index=True)

    # 文件信息
    filename = Column(String(255), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)  # 相对于技能根目录
    file_type = Column(String(50), nullable=False)  # python, javascript, markdown, config

    # 文件内容
    content = Column(Text, nullable=True)

    # Git 信息
    git_last_commit = Column(String(40), nullable=True)
    git_last_modified = Column(DateTime, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    skill = relationship("Skill", back_populates="files")

    def __repr__(self):
        return f"<SkillFile(id={self.id}, filename={self.filename}, skill_id={self.skill_id})>"


class SkillExecution(Base):
    """技能执行记录"""
    __tablename__ = "skill_executions"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 执行信息
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, running, success, failed
    input_params = Column(JSON, nullable=True)  # 输入参数
    output_result = Column(Text, nullable=True)  # 输出结果
    error_message = Column(Text, nullable=True)  # 错误信息

    # 执行环境
    container_id = Column(String(64), nullable=True)  # Docker 容器 ID
    execution_time = Column(Integer, nullable=True)  # 执行时间（毫秒）

    # 时间戳
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    skill = relationship("Skill", back_populates="executions")
    user = relationship("User", back_populates="skill_executions")
    logs = relationship("SkillExecutionLog", back_populates="execution", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SkillExecution(id={self.id}, skill_id={self.skill_id}, status={self.status})>"


class SkillExecutionLog(Base):
    """技能执行日志"""
    __tablename__ = "skill_execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("skill_executions.id"), nullable=False, index=True)

    # 日志信息
    log_level = Column(String(20), default="INFO", nullable=False)  # DEBUG, INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)  # 额外元数据

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    execution = relationship("SkillExecution", back_populates="logs")

    def __repr__(self):
        return f"<SkillExecutionLog(id={self.id}, execution_id={self.execution_id}, level={self.log_level})>"
