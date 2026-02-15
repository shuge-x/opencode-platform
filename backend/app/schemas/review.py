"""
评论、评分和收藏 Pydantic 模型
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from datetime import datetime


# ============= 评论相关 =============

class ReviewCreateRequest(BaseModel):
    """创建评论请求"""
    rating: int = Field(..., ge=1, le=5, description="评分 1-5 星")
    title: Optional[str] = Field(None, max_length=200, description="评论标题")
    content: Optional[str] = Field(None, max_length=5000, description="评论内容")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        # 如果有标题但没有内容，给出警告
        return v


class ReviewUpdateRequest(BaseModel):
    """更新评论请求"""
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分 1-5 星")
    title: Optional[str] = Field(None, max_length=200, description="评论标题")
    content: Optional[str] = Field(None, max_length=5000, description="评论内容")


class ReviewResponse(BaseModel):
    """评论响应"""
    id: int
    published_skill_id: int
    user_id: int
    rating: int
    title: Optional[str] = None
    content: Optional[str] = None
    status: str
    is_edited: bool
    created_at: datetime
    updated_at: datetime
    
    # 用户信息（可选，在列表时填充）
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    """评论列表响应"""
    items: List[ReviewResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
    avg_rating: Optional[float] = None
    rating_distribution: Optional[Dict[int, int]] = None


# ============= 评分相关 =============

class RatingRequest(BaseModel):
    """评分请求"""
    rating: int = Field(..., ge=1, le=5, description="评分 1-5 星")


class RatingResponse(BaseModel):
    """评分响应"""
    skill_id: int
    user_rating: Optional[int] = None
    avg_rating: float
    rating_count: int
    rating_distribution: Dict[int, int]


class RatingStatsResponse(BaseModel):
    """评分统计响应"""
    skill_id: int
    avg_rating: float
    rating_count: int
    rating_distribution: Dict[int, int]
    updated_at: str


# ============= 收藏相关 =============

class BookmarkCreateRequest(BaseModel):
    """创建收藏请求"""
    notes: Optional[str] = Field(None, max_length=500, description="收藏备注")


class BookmarkUpdateRequest(BaseModel):
    """更新收藏请求"""
    notes: Optional[str] = Field(None, max_length=500, description="收藏备注")


class BookmarkResponse(BaseModel):
    """收藏响应"""
    id: int
    published_skill_id: int
    user_id: int
    notes: Optional[str] = None
    created_at: datetime
    
    # 技能信息（在列表时填充）
    skill_name: Optional[str] = None
    skill_slug: Optional[str] = None
    skill_description: Optional[str] = None
    skill_rating: Optional[float] = None
    skill_download_count: Optional[int] = None
    skill_category: Optional[str] = None

    class Config:
        from_attributes = True


class BookmarkListResponse(BaseModel):
    """收藏列表响应"""
    items: List[BookmarkResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
