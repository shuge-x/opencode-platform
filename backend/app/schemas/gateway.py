"""
API网关相关的Pydantic schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re


# ==================== 路由配置 Schemas ====================

class GatewayRouteBase(BaseModel):
    """网关路由基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="路由名称")
    description: Optional[str] = Field(None, description="路由描述")
    path: str = Field(..., min_length=1, max_length=500, description="路由路径")
    service_name: str = Field(..., min_length=1, max_length=100, description="目标服务名称")
    service_url: str = Field(..., min_length=1, max_length=500, description="目标服务URL")
    methods: List[str] = Field(default=["GET"], description="允许的HTTP方法")
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v):
        if not v.startswith('/'):
            raise ValueError('Path must start with /')
        return v
    
    @field_validator('methods')
    @classmethod
    def validate_methods(cls, v):
        valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
        for method in v:
            if method.upper() not in valid_methods:
                raise ValueError(f'Invalid HTTP method: {method}')
        return [m.upper() for m in v]
    
    @field_validator('service_url')
    @classmethod
    def validate_service_url(cls, v):
        if not re.match(r'^https?://', v):
            raise ValueError('Service URL must start with http:// or https://')
        return v.rstrip('/')


class GatewayRouteCreate(GatewayRouteBase):
    """网关路由创建模型"""
    rate_limit: Optional[int] = Field(None, ge=1, description="每分钟请求限制")
    rate_limit_window: int = Field(default=60, ge=1, description="限流窗口(秒)")
    require_auth: bool = Field(default=True, description="是否需要JWT认证")
    require_api_key: bool = Field(default=False, description="是否需要API密钥")
    cors_enabled: bool = Field(default=True, description="是否启用CORS")
    timeout_ms: int = Field(default=30000, ge=100, le=300000, description="超时时间(毫秒)")
    retry_count: int = Field(default=3, ge=0, le=10, description="重试次数")
    priority: int = Field(default=100, ge=1, le=1000, description="路由优先级")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")
    metadata: Optional[dict] = Field(default=None, description="额外元数据")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "user-service",
                "description": "用户服务路由",
                "path": "/api/v1/users",
                "service_name": "user-service",
                "service_url": "http://user-service:8080",
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "rate_limit": 100,
                "rate_limit_window": 60,
                "require_auth": True,
                "require_api_key": False,
                "cors_enabled": True,
                "timeout_ms": 30000,
                "retry_count": 3,
                "priority": 100,
                "tags": ["core", "users"]
            }
        }
    )


class GatewayRouteUpdate(BaseModel):
    """网关路由更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    path: Optional[str] = Field(None, min_length=1, max_length=500)
    service_name: Optional[str] = Field(None, min_length=1, max_length=100)
    service_url: Optional[str] = Field(None, min_length=1, max_length=500)
    methods: Optional[List[str]] = None
    rate_limit: Optional[int] = Field(None, ge=1)
    rate_limit_window: Optional[int] = Field(None, ge=1)
    require_auth: Optional[bool] = None
    require_api_key: Optional[bool] = None
    cors_enabled: Optional[bool] = None
    timeout_ms: Optional[int] = Field(None, ge=100, le=300000)
    retry_count: Optional[int] = Field(None, ge=0, le=10)
    priority: Optional[int] = Field(None, ge=1, le=1000)
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v):
        if v is not None and not v.startswith('/'):
            raise ValueError('Path must start with /')
        return v
    
    @field_validator('service_url')
    @classmethod
    def validate_service_url(cls, v):
        if v is not None and not re.match(r'^https?://', v):
            raise ValueError('Service URL must start with http:// or https://')
        return v.rstrip('/') if v else None


class GatewayRouteResponse(GatewayRouteBase):
    """网关路由响应模型"""
    id: int
    rate_limit: Optional[int] = None
    rate_limit_window: int = 60
    require_auth: bool = True
    require_api_key: bool = False
    cors_enabled: bool = True
    timeout_ms: int = 30000
    retry_count: int = 3
    priority: int = 100
    is_active: bool = True
    tags: List[str] = []
    metadata: dict = {}
    external_id: Optional[str] = None
    sync_status: str = "pending"
    last_sync_at: Optional[datetime] = None
    sync_error: Optional[str] = None
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class GatewayRouteListResponse(BaseModel):
    """网关路由列表响应"""
    total: int = Field(..., description="总数")
    items: List[GatewayRouteResponse] = Field(..., description="路由列表")


# ==================== API密钥 Schemas ====================

class ApiKeyCreate(BaseModel):
    """API密钥创建模型"""
    name: str = Field(..., min_length=1, max_length=100, description="密钥名称")
    description: Optional[str] = Field(None, description="密钥描述")
    scopes: List[str] = Field(default=["read"], description="权限范围")
    allowed_routes: Optional[List[str]] = Field(None, description="允许访问的路由")
    allowed_ips: Optional[List[str]] = Field(None, description="IP白名单")
    rate_limit: Optional[int] = Field(None, ge=1, description="每分钟请求限制")
    daily_limit: Optional[int] = Field(None, ge=1, description="每日请求限制")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    
    @field_validator('scopes')
    @classmethod
    def validate_scopes(cls, v):
        valid_scopes = {"read", "write", "admin", "execute"}
        for scope in v:
            if scope not in valid_scopes:
                raise ValueError(f'Invalid scope: {scope}. Valid scopes: {valid_scopes}')
        return v
    
    @field_validator('allowed_ips')
    @classmethod
    def validate_ips(cls, v):
        if v is None:
            return v
        ip_pattern = re.compile(
            r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
            r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?:/\d{1,2})?$'
        )
        for ip in v:
            if not ip_pattern.match(ip):
                raise ValueError(f'Invalid IP address or CIDR: {ip}')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Production API Key",
                "description": "用于生产环境的API密钥",
                "scopes": ["read", "execute"],
                "allowed_routes": ["/api/v1/skills/*", "/api/v1/sessions/*"],
                "allowed_ips": ["192.168.1.0/24"],
                "rate_limit": 1000,
                "daily_limit": 100000,
                "expires_at": "2025-12-31T23:59:59Z"
            }
        }
    )


class ApiKeyResponse(BaseModel):
    """API密钥响应模型"""
    id: int
    name: str
    key_prefix: str = Field(..., description="密钥前缀(用于识别)")
    description: Optional[str] = None
    scopes: List[str] = []
    allowed_routes: List[str] = []
    allowed_ips: List[str] = []
    rate_limit: Optional[int] = None
    daily_limit: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True
    total_requests: int = 0
    last_used_at: Optional[datetime] = None
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreateResponse(ApiKeyResponse):
    """API密钥创建响应（包含完整密钥）"""
    key: str = Field(..., description="完整的API密钥（仅创建时显示一次）")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Production API Key",
                "key": "oc_live_sk_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
                "key_prefix": "oc_live_",
                "scopes": ["read", "execute"],
                "is_active": True
            }
        }
    )


class ApiKeyListResponse(BaseModel):
    """API密钥列表响应"""
    total: int = Field(..., description="总数")
    items: List[ApiKeyResponse] = Field(..., description="密钥列表")


# ==================== 限流相关 Schemas ====================

class RateLimitConfig(BaseModel):
    """限流配置"""
    enabled: bool = Field(default=True, description="是否启用限流")
    requests_per_minute: Optional[int] = Field(None, ge=1, description="每分钟请求数")
    requests_per_hour: Optional[int] = Field(None, ge=1, description="每小时请求数")
    requests_per_day: Optional[int] = Field(None, ge=1, description="每日请求数")
    burst_size: Optional[int] = Field(None, ge=1, description="突发请求数")


class RateLimitStatus(BaseModel):
    """限流状态"""
    key: str = Field(..., description="限流键")
    limit: int = Field(..., description="限制值")
    remaining: int = Field(..., description="剩余请求数")
    reset_at: datetime = Field(..., description="重置时间")
    blocked: bool = Field(..., description="是否被限制")


# ==================== 网关状态 Schemas ====================

class GatewayServiceStatus(BaseModel):
    """网关服务状态"""
    name: str = Field(..., description="服务名称")
    status: str = Field(..., description="服务状态")
    routes_count: int = Field(..., description="路由数量")
    healthy: bool = Field(..., description="是否健康")
    last_check: datetime = Field(..., description="最后检查时间")


class GatewayStats(BaseModel):
    """网关统计"""
    total_routes: int = Field(..., description="总路由数")
    active_routes: int = Field(..., description="活跃路由数")
    total_api_keys: int = Field(..., description="总API密钥数")
    active_api_keys: int = Field(..., description="活跃API密钥数")
    requests_today: int = Field(..., description="今日请求数")
    blocked_requests_today: int = Field(..., description="今日被限流请求数")
    services: List[GatewayServiceStatus] = Field(default=[], description="服务状态列表")


# ==================== 认证相关 Schemas ====================

class ApiKeyAuth(BaseModel):
    """API密钥认证请求"""
    api_key: str = Field(..., description="API密钥")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "api_key": "oc_live_sk_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
            }
        }
    )


class AuthValidationResponse(BaseModel):
    """认证验证响应"""
    valid: bool = Field(..., description="是否有效")
    auth_type: str = Field(..., description="认证类型(jwt/api_key)")
    user_id: Optional[int] = Field(None, description="用户ID")
    scopes: List[str] = Field(default=[], description="权限范围")
    rate_limit: Optional[int] = Field(None, description="限流配置")
    message: Optional[str] = Field(None, description="额外信息")
