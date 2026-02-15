"""
分类 Pydantic 模型
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class CategoryBase(BaseModel):
    """分类基础模型"""
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")
    slug: Optional[str] = Field(None, max_length=60, description="分类slug")
    description: Optional[str] = Field(None, description="分类描述")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    icon: Optional[str] = Field(None, max_length=50, description="图标名称")
    color: Optional[str] = Field(None, max_length=20, description="分类颜色")
    sort_order: int = Field(default=0, description="排序顺序")


class CategoryCreate(CategoryBase):
    """创建分类请求"""
    pass


class CategoryUpdate(BaseModel):
    """更新分类请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    """分类响应"""
    id: int
    is_active: bool
    skill_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CategoryTreeResponse(CategoryResponse):
    """分类树响应（包含子分类）"""
    children: List["CategoryTreeResponse"] = []

    class Config:
        from_attributes = True


class CategoryListResponse(BaseModel):
    """分类列表响应"""
    items: List[CategoryResponse]
    total: int


class CategoryStatsResponse(BaseModel):
    """分类统计响应"""
    category_id: int
    category_name: str
    skill_count: int
    download_count: int
    avg_rating: float
