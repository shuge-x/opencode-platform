"""
技能部署数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class DeploymentStatus(str, enum.Enum):
    """部署状态"""
    PENDING = "pending"  # 待部署
    BUILDING = "building"  # 构建中
    DEPLOYING = "deploying"  # 部署中
    RUNNING = "running"  # 运行中
    STOPPED = "stopped"  # 已停止
    FAILED = "failed"  # 失败
    RESTARTING = "restarting"  # 重启中


class HealthStatus(str, enum.Enum):
    """健康状态"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class Deployment(Base):
    """技能部署"""
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    
    # 关联信息
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False, index=True)
    skill_package_id = Column(Integer, ForeignKey("skill_packages.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 部署配置
    name = Column(String(100), nullable=False, index=True)  # 部署名称
    slug = Column(String(120), nullable=False, unique=True, index=True)  # 唯一标识
    
    # Docker 镜像信息
    image_name = Column(String(255), nullable=False)  # 镜像名称
    image_tag = Column(String(50), default="latest", nullable=False)  # 镜像标签
    image_id = Column(String(100), nullable=True)  # Docker 镜像 ID
    
    # 容器配置
    container_id = Column(String(100), nullable=True)  # Docker 容器 ID
    container_name = Column(String(100), nullable=True)  # 容器名称
    ports = Column(JSON, nullable=True)  # 端口映射 {"8080": "8080"}
    environment = Column(JSON, nullable=True)  # 环境变量
    volumes = Column(JSON, nullable=True)  # 卷挂载
    networks = Column(JSON, nullable=True)  # 网络配置
    resource_limits = Column(JSON, nullable=True)  # 资源限制 {cpu, memory}
    
    # Compose 配置
    compose_config = Column(JSON, nullable=True)  # Docker Compose 配置
    compose_file_path = Column(String(500), nullable=True)  # Compose 文件路径
    
    # 状态信息
    status = Column(
        Enum(DeploymentStatus),
        default=DeploymentStatus.PENDING,
        nullable=False,
        index=True
    )
    health_status = Column(
        Enum(HealthStatus),
        default=HealthStatus.UNKNOWN,
        nullable=False
    )
    
    # 运行时信息
    started_at = Column(DateTime, nullable=True)  # 启动时间
    stopped_at = Column(DateTime, nullable=True)  # 停止时间
    last_health_check = Column(DateTime, nullable=True)  # 最后健康检查时间
    restart_count = Column(Integer, default=0, nullable=False)  # 重启次数
    
    # 统计信息
    cpu_usage = Column(String(20), nullable=True)  # CPU 使用率
    memory_usage = Column(String(20), nullable=True)  # 内存使用
    network_io = Column(JSON, nullable=True)  # 网络 I/O
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    error_stack = Column(Text, nullable=True)
    
    # 自动重启配置
    auto_restart = Column(Boolean, default=True, nullable=False)
    max_restart_attempts = Column(Integer, default=3, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    skill = relationship("Skill", backref="deployments")
    user = relationship("User", backref="deployments")
    health_checks = relationship("DeploymentHealthCheck", back_populates="deployment", cascade="all, delete-orphan")
    logs = relationship("DeploymentLog", back_populates="deployment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Deployment(id={self.id}, name={self.name}, status={self.status})>"


class DeploymentHealthCheck(Base):
    """部署健康检查记录"""
    __tablename__ = "deployment_health_checks"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id"), nullable=False, index=True)
    
    # 健康状态
    status = Column(Enum(HealthStatus), nullable=False)
    
    # 检查详情
    response_time_ms = Column(Integer, nullable=True)  # 响应时间（毫秒）
    http_status = Column(Integer, nullable=True)  # HTTP 状态码
    check_type = Column(String(50), default="http", nullable=False)  # 检查类型
    
    # 详细信息
    details = Column(JSON, nullable=True)  # 详细检查结果
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    
    # 时间戳
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关系
    deployment = relationship("Deployment", back_populates="health_checks")
    
    def __repr__(self):
        return f"<DeploymentHealthCheck(deployment_id={self.deployment_id}, status={self.status})>"


class DeploymentLog(Base):
    """部署日志"""
    __tablename__ = "deployment_logs"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id"), nullable=False, index=True)
    
    # 日志信息
    log_type = Column(String(20), default="stdout", nullable=False)  # stdout, stderr, system
    content = Column(Text, nullable=True)
    
    # 时间戳
    logged_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关系
    deployment = relationship("Deployment", back_populates="logs")
    
    def __repr__(self):
        return f"<DeploymentLog(deployment_id={self.deployment_id}, type={self.log_type})>"


class DockerfileTemplate(Base):
    """Dockerfile 模板"""
    __tablename__ = "dockerfile_templates"

    id = Column(Integer, primary_key=True, index=True)
    
    # 模板信息
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # 模板内容
    content = Column(Text, nullable=False)  # Dockerfile 内容
    variables = Column(JSON, nullable=True)  # 可替换变量定义
    
    # 分类
    language = Column(String(50), nullable=True, index=True)  # 编程语言
    runtime = Column(String(50), nullable=True)  # 运行时环境
    category = Column(String(50), nullable=True)  # 分类
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<DockerfileTemplate(name={self.name}, language={self.language})>"
