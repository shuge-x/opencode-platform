"""
技能相关的Pydantic schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class SkillBase(BaseModel):
    """技能基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="技能名称")
    description: Optional[str] = Field(None, description="技能描述")
    category: Optional[str] = Field(None, max_length=50, description="分类")
    prompt_template: str = Field(..., description="提示词模板")
    tags: Optional[List[str]] = Field(default=[], description="标签")
    is_public: bool = Field(default=False, description="是否公开")


class SkillCreate(SkillBase):
    """技能创建模型"""
    config: Optional[dict] = Field(default={}, description="技能配置")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "代码审查助手",
                "description": "帮助审查代码质量和安全性",
                "category": "development",
                "prompt_template": "请审查以下代码：\n{code}\n\n关注点：\n1. 代码质量\n2. 安全性\n3. 性能",
                "tags": ["code", "review", "development"],
                "is_public": False,
                "config": {}
            }
        }
    )


class SkillUpdate(BaseModel):
    """技能更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    prompt_template: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "更新的技能名称",
                "description": "更新的描述"
            }
        }
    )


class SkillResponse(SkillBase):
    """技能响应模型"""
    id: int
    slug: str
    user_id: int
    config: Optional[dict] = {}
    is_active: bool
    is_verified: bool
    use_count: int
    like_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SkillListResponse(BaseModel):
    """技能列表响应"""
    items: List[SkillResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 5,
                "page": 1,
                "page_size": 20,
                "has_more": False
            }
        }
    )
