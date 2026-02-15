"""
技能部署 Schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class DeploymentStatus(str, Enum):
    """部署状态"""
    PENDING = "pending"
    BUILDING = "building"
    DEPLOYING = "deploying"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    RESTARTING = "restarting"


class HealthStatus(str, Enum):
    """健康状态"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


# ============= 部署请求 Schemas =============

class DeployRequest(BaseModel):
    """部署技能请求"""
    skill_id: int = Field(..., description="技能 ID")
    skill_package_id: Optional[int] = Field(None, description="技能包 ID（可选，默认使用最新版本）")
    name: str = Field(..., min_length=1, max_length=100, description="部署名称")
    
    # 容器配置
    ports: Optional[Dict[str, str]] = Field(None, description="端口映射")
    environment: Optional[Dict[str, str]] = Field(None, description="环境变量")
    volumes: Optional[Dict[str, str]] = Field(None, description="卷挂载")
    
    # 资源限制
    cpu_limit: Optional[str] = Field(None, description="CPU 限制，如 '1.0'")
    memory_limit: Optional[str] = Field(None, description="内存限制，如 '512m'")
    
    # 其他配置
    auto_restart: bool = Field(True, description="是否自动重启")
    max_restart_attempts: int = Field(3, ge=0, le=10, description="最大重启尝试次数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "skill_id": 1,
                "name": "my-skill-app",
                "ports": {"8080": "8080"},
                "environment": {"DEBUG": "false"},
                "cpu_limit": "0.5",
                "memory_limit": "256m",
                "auto_restart": True
            }
        }


class DeploymentUpdate(BaseModel):
    """更新部署配置"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    ports: Optional[Dict[str, str]] = None
    environment: Optional[Dict[str, str]] = None
    volumes: Optional[Dict[str, str]] = None
    cpu_limit: Optional[str] = None
    memory_limit: Optional[str] = None
    auto_restart: Optional[bool] = None
    max_restart_attempts: Optional[int] = Field(None, ge=0, le=10)


# ============= 部署响应 Schemas =============

class DeploymentResponse(BaseModel):
    """部署详情响应"""
    id: int
    skill_id: int
    skill_package_id: Optional[int]
    user_id: int
    name: str
    slug: str
    
    # 镜像和容器信息
    image_name: str
    image_tag: str
    image_id: Optional[str]
    container_id: Optional[str]
    container_name: Optional[str]
    
    # 配置
    ports: Optional[Dict[str, str]]
    environment: Optional[Dict[str, str]]
    volumes: Optional[Dict[str, str]]
    resource_limits: Optional[Dict[str, str]]
    
    # 状态
    status: DeploymentStatus
    health_status: HealthStatus
    
    # 运行时信息
    started_at: Optional[datetime]
    stopped_at: Optional[datetime]
    last_health_check: Optional[datetime]
    restart_count: int
    
    # 统计
    cpu_usage: Optional[str]
    memory_usage: Optional[str]
    
    # 错误
    error_message: Optional[str]
    
    # 配置
    auto_restart: bool
    max_restart_attempts: int
    
    # 时间戳
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DeploymentListResponse(BaseModel):
    """部署列表响应"""
    items: List[DeploymentResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class DeploymentBrief(BaseModel):
    """部署简要信息"""
    id: int
    name: str
    status: DeploymentStatus
    health_status: HealthStatus
    image_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= 健康检查 Schemas =============

class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    deployment_id: int
    status: HealthStatus
    response_time_ms: Optional[int]
    http_status: Optional[int]
    check_type: str
    details: Optional[Dict[str, Any]]
    error_message: Optional[str]
    checked_at: datetime
    
    class Config:
        from_attributes = True


class HealthCheckListResponse(BaseModel):
    """健康检查历史列表"""
    items: List[HealthCheckResponse]
    total: int
    page: int
    page_size: int


class HealthStatusSummary(BaseModel):
    """健康状态摘要"""
    total_deployments: int
    healthy_count: int
    unhealthy_count: int
    unknown_count: int
    health_percentage: float


# ============= 日志 Schemas =============

class LogEntry(BaseModel):
    """单条日志"""
    log_type: str
    content: str
    logged_at: datetime


class DeploymentLogResponse(BaseModel):
    """部署日志响应"""
    deployment_id: int
    logs: List[LogEntry]
    has_more: bool
    last_timestamp: Optional[datetime]


class LogQuery(BaseModel):
    """日志查询参数"""
    since: Optional[datetime] = None
    tail: Optional[int] = Field(100, ge=1, le=10000)
    log_type: Optional[str] = None


# ============= Dockerfile 模板 Schemas =============

class DockerfileTemplateCreate(BaseModel):
    """创建 Dockerfile 模板"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    content: str = Field(..., min_length=1)
    variables: Optional[List[Dict[str, str]]] = None
    language: Optional[str] = None
    runtime: Optional[str] = None
    category: Optional[str] = None
    is_default: bool = False


class DockerfileTemplateUpdate(BaseModel):
    """更新 Dockerfile 模板"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    content: Optional[str] = Field(None, min_length=1)
    variables: Optional[List[Dict[str, str]]] = None
    language: Optional[str] = None
    runtime: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class DockerfileTemplateResponse(BaseModel):
    """Dockerfile 模板响应"""
    id: int
    name: str
    description: Optional[str]
    content: str
    variables: Optional[List[Dict[str, str]]]
    language: Optional[str]
    runtime: Optional[str]
    category: Optional[str]
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DockerfileTemplateListResponse(BaseModel):
    """Dockerfile 模板列表"""
    items: List[DockerfileTemplateResponse]
    total: int


# ============= 镜像构建 Schemas =============

class BuildRequest(BaseModel):
    """构建镜像请求"""
    skill_id: int
    skill_package_id: Optional[int] = None
    template_id: Optional[int] = None
    custom_dockerfile: Optional[str] = None
    build_args: Optional[Dict[str, str]] = None
    tag: Optional[str] = None


class BuildProgress(BaseModel):
    """构建进度"""
    build_id: str
    status: str
    step: Optional[str]
    message: Optional[str]
    progress: Optional[float]
    error: Optional[str]


class BuildResponse(BaseModel):
    """构建响应"""
    build_id: str
    image_name: str
    image_tag: str
    image_id: Optional[str]
    status: str
    build_log: Optional[str]
    created_at: datetime


# ============= 容器操作 Schemas =============

class ContainerStats(BaseModel):
    """容器统计信息"""
    container_id: str
    cpu_percent: float
    memory_usage: str
    memory_percent: float
    network_rx: str
    network_tx: str
    block_read: str
    block_write: str
    timestamp: datetime


class ContainerInfo(BaseModel):
    """容器信息"""
    container_id: str
    name: str
    image: str
    status: str
    state: str
    created: datetime
    ports: List[Dict[str, Any]]
    labels: Dict[str, str]


class RestartRequest(BaseModel):
    """重启请求"""
    force: bool = Field(False, description="是否强制重启")
    timeout: int = Field(10, ge=0, le=300, description="超时时间（秒）")


class RestartResponse(BaseModel):
    """重启响应"""
    deployment_id: int
    status: DeploymentStatus
    message: str
    restarted_at: datetime


# ============= Compose 配置 Schemas =============

class ComposeGenerateRequest(BaseModel):
    """生成 Compose 配置请求"""
    deployment_id: int
    include_volumes: bool = True
    include_networks: bool = True
    custom_config: Optional[Dict[str, Any]] = None


class ComposeConfigResponse(BaseModel):
    """Compose 配置响应"""
    deployment_id: int
    compose_yaml: str
    compose_json: Dict[str, Any]
    file_path: Optional[str]
