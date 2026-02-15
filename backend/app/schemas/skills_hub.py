"""
Skills Hub Pydantic 模型
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# ============= 发布技能 =============

class SkillPublishRequest(BaseModel):
    """发布技能请求"""
    skill_id: int = Field(..., description="技能ID")
    name: str = Field(..., min_length=1, max_length=100, description="技能名称")
    description: Optional[str] = Field(None, description="技能描述")
    category: Optional[str] = Field(None, max_length=50, description="分类")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    
    # 定价
    price: Decimal = Field(default=Decimal("0.00"), description="价格")
    currency: str = Field(default="USD", max_length=10, description="货币")
    
    # 元数据
    homepage_url: Optional[str] = Field(None, description="主页URL")
    repository_url: Optional[str] = Field(None, description="仓库URL")
    documentation_url: Optional[str] = Field(None, description="文档URL")
    license: str = Field(default="MIT", description="许可证")
    
    # 版本信息
    version: str = Field(default="1.0.0", description="版本号")
    release_notes: Optional[str] = Field(None, description="发布说明")
    changelog: Optional[str] = Field(None, description="变更日志")
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('Price cannot be negative')
        return v


class PublishedSkillResponse(BaseModel):
    """已发布技能响应"""
    id: int
    skill_id: int
    publisher_id: int
    name: str
    slug: str
    description: Optional[str] = None
    version: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    price: Decimal
    currency: str
    status: str
    is_public: bool
    is_featured: bool
    download_count: int
    install_count: int
    rating: Decimal
    rating_count: int
    homepage_url: Optional[str] = None
    repository_url: Optional[str] = None
    documentation_url: Optional[str] = None
    license: str
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============= 技能包上传 =============

class SkillPackageResponse(BaseModel):
    """技能包响应"""
    id: int
    published_skill_id: int
    version: str
    version_code: int
    file_size: int
    checksum: str
    dependencies: Optional[List[Dict[str, Any]]] = None
    min_platform_version: Optional[str] = None
    release_notes: Optional[str] = None
    changelog: Optional[str] = None
    is_active: bool
    is_latest: bool
    download_count: int
    published_at: datetime
    download_url: Optional[str] = None  # 预签名下载URL

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    """上传响应"""
    message: str
    package_id: int
    version: str
    file_size: int
    checksum: str


# ============= 版本管理 =============

class VersionCreateRequest(BaseModel):
    """创建新版本请求"""
    version: str = Field(..., description="版本号，如 1.1.0")
    release_notes: Optional[str] = Field(None, description="发布说明")
    changelog: Optional[str] = Field(None, description="变更日志")
    dependencies: Optional[List[Dict[str, Any]]] = Field(None, description="依赖列表")
    min_platform_version: Optional[str] = Field(None, description="最低平台版本")
    
    @field_validator('version')
    @classmethod
    def validate_version(cls, v):
        # 简单的版本号验证
        parts = v.split('.')
        if len(parts) != 3:
            raise ValueError('Version must be in format: X.Y.Z')
        for part in parts:
            if not part.isdigit():
                raise ValueError('Version parts must be numbers')
        return v


class VersionListResponse(BaseModel):
    """版本列表响应"""
    items: List[SkillPackageResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============= 权限管理 =============

class PermissionGrantRequest(BaseModel):
    """授予权限请求"""
    user_id: int = Field(..., description="用户ID")
    permission_type: str = Field(..., description="权限类型: owner, admin, write, read")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    
    @field_validator('permission_type')
    @classmethod
    def validate_permission_type(cls, v):
        allowed = ['owner', 'admin', 'write', 'read']
        if v not in allowed:
            raise ValueError(f'Permission type must be one of: {allowed}')
        return v


class PermissionResponse(BaseModel):
    """权限响应"""
    id: int
    published_skill_id: int
    user_id: int
    permission_type: str
    granted_by: Optional[int] = None
    granted_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============= 列表和搜索 =============

class SkillHubListResponse(BaseModel):
    """技能市场列表响应"""
    items: List[PublishedSkillResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class SkillHubSearchRequest(BaseModel):
    """技能市场搜索请求"""
    query: Optional[str] = Field(None, description="搜索关键词")
    category: Optional[str] = Field(None, description="分类")
    tags: Optional[List[str]] = Field(None, description="标签")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="最低评分")
    price_min: Optional[Decimal] = Field(None, description="最低价格")
    price_max: Optional[Decimal] = Field(None, description="最高价格")
    is_free: Optional[bool] = Field(None, description="只看免费")
    sort_by: Optional[str] = Field("download_count", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方向: asc, desc")
