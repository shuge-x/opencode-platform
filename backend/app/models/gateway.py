"""
API网关数据模型

存储路由配置和API密钥
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Text, JSON, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class GatewayRoute(Base):
    """
    网关路由模型
    
    存储API路由配置
    """
    __tablename__ = "gateway_routes"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 路由基本信息
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # 路由配置
    path: Mapped[str] = mapped_column(String(500), nullable=False)  # 例如 /api/v1/users
    service_name: Mapped[str] = mapped_column(String(100), nullable=False)  # 目标服务名
    service_url: Mapped[str] = mapped_column(String(500), nullable=False)  # 目标服务URL
    methods: Mapped[List[str]] = mapped_column(JSON, default=list)  # 允许的HTTP方法
    
    # 插件配置
    rate_limit: Mapped[Optional[int]] = mapped_column(Integer, default=None)  # 请求/分钟
    rate_limit_window: Mapped[Optional[int]] = mapped_column(Integer, default=60)  # 窗口大小(秒)
    require_auth: Mapped[bool] = mapped_column(Boolean, default=True)  # 是否需要认证
    require_api_key: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否需要API密钥
    cors_enabled: Mapped[bool] = mapped_column(Boolean, default=True)  # 是否启用CORS
    
    # 超时和重试
    timeout_ms: Mapped[int] = mapped_column(Integer, default=30000)  # 超时时间(毫秒)
    retry_count: Mapped[int] = mapped_column(Integer, default=3)  # 重试次数
    
    # 优先级和状态
    priority: Mapped[int] = mapped_column(Integer, default=100)  # 路由优先级
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 元数据
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Kong/Traefik同步状态
    external_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)  # 外部网关ID
    sync_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/synced/failed
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sync_error: Mapped[Optional[str]] = mapped_column(Text)
    
    # 所属用户
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    user = relationship("User", backref="gateway_routes")
    
    def __repr__(self) -> str:
        return f"<GatewayRoute(id={self.id}, name={self.name}, path={self.path})>"


class ApiKey(Base):
    """
    API密钥模型
    
    用于API访问认证
    """
    __tablename__ = "api_keys"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 密钥信息
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(8), index=True)  # 密钥前缀，用于快速查找
    
    # 描述
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # 权限范围
    scopes: Mapped[List[str]] = mapped_column(JSON, default=list)  # 权限范围列表
    allowed_routes: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)  # 允许的路由
    allowed_ips: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)  # 允许的IP白名单
    
    # 限流配置
    rate_limit: Mapped[Optional[int]] = mapped_column(Integer, default=None)  # 请求/分钟，None表示无限制
    daily_limit: Mapped[Optional[int]] = mapped_column(Integer, default=None)  # 每日请求限制
    
    # 有效期
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 使用统计
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # 所属用户
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    user = relationship("User", backref="api_keys")
    
    def __repr__(self) -> str:
        return f"<ApiKey(id={self.id}, name={self.name}, key_prefix={self.key_prefix})>"


class RateLimitLog(Base):
    """
    限流日志模型
    
    记录限流事件
    """
    __tablename__ = "rate_limit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 限流目标
    key_type: Mapped[str] = mapped_column(String(20), nullable=False)  # ip/user/api_key
    key_value: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    
    # 请求信息
    route_id: Mapped[Optional[int]] = mapped_column(ForeignKey("gateway_routes.id"))
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # 限流信息
    limit: Mapped[int] = mapped_column(Integer, nullable=False)
    window_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    current_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # 是否被限制
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关系
    route = relationship("GatewayRoute", backref="rate_limit_logs")
    
    def __repr__(self) -> str:
        return f"<RateLimitLog(id={self.id}, key={self.key_value}, blocked={self.blocked})>"
