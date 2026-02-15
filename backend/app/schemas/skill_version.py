"""
技能版本 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class VersionCreate(BaseModel):
    """创建版本（提交变更）"""
    message: str = Field(..., min_length=1, max_length=500, description="提交信息")
    files: Optional[Dict[str, str]] = Field(None, description="要提交的文件 {文件名: 内容}")
    version_name: Optional[str] = Field(None, max_length=100, description="版本名称（如 v1.0.0）")
    is_release: bool = Field(False, description="是否标记为正式发布版本")


class VersionRestore(BaseModel):
    """版本回退请求"""
    create_backup: bool = Field(True, description="是否创建备份分支")


class VersionCompare(BaseModel):
    """版本对比请求"""
    from_commit: str = Field(..., description="源版本 commit hash")
    to_commit: str = Field(..., description="目标版本 commit hash")


class FileDiffResponse(BaseModel):
    """文件差异响应"""
    file_path: str
    change_type: str  # A (added), M (modified), D (deleted), R (renamed)
    old_file: Optional[str] = None
    new_file: Optional[str] = None
    diff: Optional[str] = None  # diff 格式的差异

    class Config:
        from_attributes = True


class CommitInfo(BaseModel):
    """提交信息"""
    hash: str
    short_hash: str
    message: str
    timestamp: str
    author: Optional[Dict[str, str]] = None


class VersionResponse(BaseModel):
    """版本响应"""
    id: int
    skill_id: int
    user_id: int
    version_name: Optional[str] = None
    commit_hash: str
    short_hash: str
    commit_message: Optional[str] = None
    is_release: bool
    is_latest: bool
    files_changed: int
    additions: int
    deletions: int
    created_at: datetime
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm_with_short_hash(cls, obj):
        """创建响应并添加短哈希"""
        data = {
            "id": obj.id,
            "skill_id": obj.skill_id,
            "user_id": obj.user_id,
            "version_name": obj.version_name,
            "commit_hash": obj.commit_hash,
            "short_hash": obj.commit_hash[:7],
            "commit_message": obj.commit_message,
            "is_release": obj.is_release,
            "is_latest": obj.is_latest,
            "files_changed": obj.files_changed,
            "additions": obj.additions,
            "deletions": obj.deletions,
            "created_at": obj.created_at
        }
        return cls(**data)


class VersionDetailResponse(BaseModel):
    """版本详情响应（包含文件变更）"""
    id: Optional[int] = None
    skill_id: int
    commit_hash: str
    short_hash: str
    message: str
    author: Optional[Dict[str, str]] = None
    timestamp: str
    parents: List[str] = []
    file_changes: List[Dict[str, Any]] = []
    is_release: bool = False
    version_name: Optional[str] = None


class VersionListResponse(BaseModel):
    """版本列表响应"""
    items: List[VersionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class VersionCompareResponse(BaseModel):
    """版本对比响应"""
    from_commit: CommitInfo
    to_commit: CommitInfo
    files_changed: int
    diffs: List[FileDiffResponse]


class VersionRestoreResponse(BaseModel):
    """版本恢复响应"""
    success: bool
    restored_to: str
    previous_commit: Optional[str] = None
    message: str
    backup_branch: Optional[str] = None


class RepoStatusResponse(BaseModel):
    """仓库状态响应"""
    initialized: bool
    current_branch: Optional[str] = None
    current_commit: Optional[str] = None
    is_dirty: bool = False
    untracked_files: List[str] = []
    modified_files: List[str] = []
    staged_files: List[str] = []
    message: Optional[str] = None


class BranchResponse(BaseModel):
    """分支响应"""
    name: str
    commit_hash: str
    is_current: bool


class BranchCreate(BaseModel):
    """创建分支请求"""
    branch_name: str = Field(..., min_length=1, max_length=100, description="分支名称")
    from_commit: Optional[str] = Field(None, description="从指定提交创建")


class BranchSwitch(BaseModel):
    """切换分支请求"""
    branch_name: str = Field(..., description="目标分支名称")
