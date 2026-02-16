"""
技能 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SkillCreate(BaseModel):
    """创建技能"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    prompt_template: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    slug: Optional[str] = Field(None, max_length=120)
    skill_type: str = "custom"
    config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_public: bool = False


class SkillUpdate(BaseModel):
    """更新技能"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    prompt_template: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    slug: Optional[str] = Field(None, max_length=120)
    config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


class SkillFileCreate(BaseModel):
    """创建技能文件"""
    filename: str
    file_path: str
    file_type: str
    content: Optional[str] = None


class SkillFileUpdate(BaseModel):
    """更新技能文件"""
    content: Optional[str] = None
    filename: Optional[str] = None


class SkillFileResponse(BaseModel):
    """技能文件响应"""
    id: int
    skill_id: int
    filename: str
    file_path: str
    file_type: str
    content: Optional[str] = None
    git_last_commit: Optional[str] = None
    git_last_modified: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SkillResponse(BaseModel):
    """技能响应"""
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    prompt_template: Optional[str] = None
    category: Optional[str] = None
    slug: Optional[str] = None
    use_count: int
    version: str
    skill_type: str
    config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    git_repo_url: Optional[str] = None
    git_branch: str
    is_active: bool
    is_public: bool
    execution_count: int
    success_count: int
    failure_count: int
    created_at: datetime
    updated_at: datetime
    files: List[SkillFileResponse] = []

    class Config:
        from_attributes = True


class SkillListResponse(BaseModel):
    """技能列表响应"""
    items: List[SkillResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class SkillExecutionCreate(BaseModel):
    """创建技能执行"""
    skill_id: int
    input_params: Optional[Dict[str, Any]] = None


class SkillExecutionLogResponse(BaseModel):
    """技能执行日志响应"""
    id: int
    execution_id: int
    log_level: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SkillExecutionResponse(BaseModel):
    """技能执行响应"""
    id: int
    skill_id: int
    user_id: int
    status: str
    input_params: Optional[Dict[str, Any]] = None
    output_result: Optional[str] = None
    error_message: Optional[str] = None
    container_id: Optional[str] = None
    execution_time: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    logs: List[SkillExecutionLogResponse] = []

    class Config:
        from_attributes = True


class SkillTemplateResponse(BaseModel):
    """技能模板响应"""
    name: str
    description: str
    file_structure: Dict[str, str]  # {filename: content}
    skill_type: str
