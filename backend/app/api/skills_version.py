"""
技能版本管理 API - Sprint 9
"""
import os
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.skill import Skill, SkillFile
from app.models.skill_version import SkillVersion
from app.schemas.skill_version import (
    VersionCreate, VersionRestore, VersionCompare,
    VersionResponse, VersionDetailResponse, VersionListResponse,
    VersionCompareResponse, VersionRestoreResponse, RepoStatusResponse,
    BranchResponse, BranchCreate, BranchSwitch, FileDiffResponse, CommitInfo
)
from app.services.git_service import git_service
from datetime import datetime

router = APIRouter()


def _check_skill_permission(skill: Skill, user: User) -> bool:
    """检查用户对技能的权限"""
    return skill.user_id == user.id or user.is_superuser


async def _get_skill_with_permission(
    skill_id: int, 
    user: User, 
    db: AsyncSession
) -> Skill:
    """获取技能并检查权限"""
    result = await db.execute(
        select(Skill).where(Skill.id == skill_id)
    )
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    if not _check_skill_permission(skill, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this skill"
        )
    
    return skill


async def _ensure_repo_initialized(skill_id: int, skill: Skill, db: AsyncSession) -> None:
    """确保仓库已初始化"""
    status_result = await git_service.get_status(skill_id)
    
    if not status_result.get("initialized"):
        # 从数据库获取所有文件并初始化仓库
        files = {}
        result = await db.execute(
            select(SkillFile).where(SkillFile.skill_id == skill_id)
        )
        skill_files = result.scalars().all()
        
        for file in skill_files:
            files[file.file_path] = file.content or ""
        
        await git_service.init_repo(skill_id, files if files else None)


# ==================== 仓库状态 ====================

@router.get("/{skill_id}/repo/status", response_model=RepoStatusResponse)
async def get_repo_status(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取技能 Git 仓库状态
    
    返回仓库是否初始化、当前分支、修改状态等信息
    """
    skill = await _get_skill_with_permission(skill_id, current_user, db)
    
    status_result = await git_service.get_status(skill_id)
    return RepoStatusResponse(**status_result)


@router.post("/{skill_id}/repo/init", status_code=status.HTTP_201_CREATED)
async def init_repo(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    初始化技能的 Git 仓库
    
    如果仓库已存在，会返回现有仓库信息
    """
    skill = await _get_skill_with_permission(skill_id, current_user, db)
    
    # 获取现有文件
    files = {}
    result = await db.execute(
        select(SkillFile).where(SkillFile.skill_id == skill_id)
    )
    skill_files = result.scalars().all()
    
    for file in skill_files:
        files[file.file_path] = file.content or ""
    
    repo_path = await git_service.init_repo(skill_id, files if files else None)
    
    return {
        "message": "Repository initialized successfully",
        "repo_path": repo_path,
        "files_added": len(files)
    }


# ==================== 版本历史 ====================

@router.get("/{skill_id}/versions", response_model=VersionListResponse)
async def list_versions(
    skill_id: int,
    branch: str = Query("main", description="分支名称"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取技能版本列表
    
    - 支持分页
    - 支持按分支过滤
    - 返回版本历史
    """
    skill = await _get_skill_with_permission(skill_id, current_user, db)
    await _ensure_repo_initialized(skill_id, skill, db)
    
    offset = (page - 1) * page_size
    
    # 从 Git 获取版本历史
    commits = await git_service.get_history(skill_id, branch, page_size + 1, offset)
    
    # 从数据库获取版本元数据
    commit_hashes = [c["commit_hash"] for c in commits[:page_size]]
    result = await db.execute(
        select(SkillVersion).where(SkillVersion.commit_hash.in_(commit_hashes))
    )
    db_versions = {v.commit_hash: v for v in result.scalars().all()}
    
    # 合并数据
    items = []
    for commit in commits[:page_size]:
        db_version = db_versions.get(commit["commit_hash"])
        
        if db_version:
            items.append(VersionResponse.from_orm_with_short_hash(db_version))
        else:
            # 如果数据库中没有记录，从 Git 信息创建临时响应
            items.append(VersionResponse(
                id=0,  # 表示这是临时数据
                skill_id=skill_id,
                user_id=skill.user_id,
                version_name=None,
                commit_hash=commit["commit_hash"],
                short_hash=commit["short_hash"],
                commit_message=commit["message"],
                is_release=False,
                is_latest=(page == 1 and offset == 0 and len(items) == 0),
                files_changed=0,
                additions=0,
                deletions=0,
                created_at=datetime.fromisoformat(commit["timestamp"])
            ))
    
    # 检查是否有更多
    has_more = len(commits) > page_size
    
    return VersionListResponse(
        items=items,
        total=len(items) + (1 if has_more else 0),  # 近似值
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.get("/{skill_id}/versions/{version_id}", response_model=VersionDetailResponse)
async def get_version(
    skill_id: int,
    version_id: str,  # 可以是 commit hash 或数据库名称
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取版本详情
    
    - version_id 可以是 commit hash（完整或短格式）
    - 返回详细的文件变更信息
    """
    skill = await _get_skill_with_permission(skill_id, current_user, db)
    await _ensure_repo_initialized(skill_id, skill, db)
    
    # 从 Git 获取提交详情
    commit_data = await git_service.get_commit(skill_id, version_id)
    
    if not commit_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version '{version_id}' not found"
        )
    
    # 从数据库获取版本元数据
    result = await db.execute(
        select(SkillVersion).where(SkillVersion.commit_hash == commit_data["commit_hash"])
    )
    db_version = result.scalar_one_or_none()
    
    return VersionDetailResponse(
        id=db_version.id if db_version else None,
        skill_id=skill_id,
        commit_hash=commit_data["commit_hash"],
        short_hash=commit_data["short_hash"],
        message=commit_data["message"],
        author=commit_data["author"],
        timestamp=commit_data["timestamp"],
        parents=commit_data["parents"],
        file_changes=commit_data["file_changes"],
        is_release=db_version.is_release if db_version else False,
        version_name=db_version.version_name if db_version else None
    )


@router.post("/{skill_id}/versions", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    skill_id: int,
    version_data: VersionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建新版本（提交变更）
    
    - 提交文件变更到 Git 仓库
    - 可选择标记为正式发布版本
    - 可设置版本名称
    """
    skill = await _get_skill_with_permission(skill_id, current_user, db)
    await _ensure_repo_initialized(skill_id, skill, db)
    
    # 执行提交
    commit_result = await git_service.commit(
        skill_id=skill_id,
        message=version_data.message,
        files=version_data.files,
        author_name=current_user.username,
        author_email=current_user.email
    )
    
    if not commit_result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=commit_result.get("message", "Failed to create version")
        )
    
    # 更新之前版本的 is_latest 标志
    await db.execute(
        update(SkillVersion)
        .where(SkillVersion.skill_id == skill_id)
        .values(is_latest=False)
    )
    
    # 创建版本记录
    db_version = SkillVersion(
        skill_id=skill_id,
        user_id=current_user.id,
        version_name=version_data.version_name,
        commit_hash=commit_result["commit_hash"],
        commit_message=version_data.message,
        is_release=version_data.is_release,
        is_latest=True,
        files_changed=len(version_data.files) if version_data.files else 0
    )
    
    db.add(db_version)
    
    # 更新技能的版本号和 commit hash
    skill.git_commit_hash = commit_result["commit_hash"]
    if version_data.version_name:
        skill.version = version_data.version_name
    
    await db.commit()
    await db.refresh(db_version)
    
    return VersionResponse.from_orm_with_short_hash(db_version)


@router.post("/{skill_id}/versions/{version_id}/restore", response_model=VersionRestoreResponse)
async def restore_version(
    skill_id: int,
    version_id: str,
    restore_data: VersionRestore,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    版本回退
    
    - 将仓库恢复到指定版本
    - 可选择是否创建备份分支
    """
    skill = await _get_skill_with_permission(skill_id, current_user, db)
    await _ensure_repo_initialized(skill_id, skill, db)
    
    # 获取当前状态
    current_status = await git_service.get_status(skill_id)
    current_commit = current_status.get("current_commit")
    
    # 创建备份分支（如果需要）
    backup_branch = None
    if restore_data.create_backup and current_commit:
        import time
        backup_branch = f"backup-{int(time.time())}"
        await git_service.create_branch(skill_id, backup_branch, current_commit)
    
    # 执行恢复
    restore_result = await git_service.restore_to_commit(skill_id, version_id)
    
    if not restore_result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=restore_result.get("error", "Failed to restore version")
        )
    
    # 更新技能的 commit hash
    skill.git_commit_hash = restore_result["restored_to"]
    await db.commit()
    
    return VersionRestoreResponse(
        success=True,
        restored_to=restore_result["restored_to"],
        previous_commit=current_commit,
        message=restore_result["message"],
        backup_branch=backup_branch
    )


# ==================== 版本对比 ====================

@router.post("/{skill_id}/versions/compare", response_model=VersionCompareResponse)
async def compare_versions(
    skill_id: int,
    compare_data: VersionCompare,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    对比两个版本
    
    - 返回两个版本之间的所有文件差异
    - 差异以 diff 格式返回
    """
    skill = await _get_skill_with_permission(skill_id, current_user, db)
    await _ensure_repo_initialized(skill_id, skill, db)
    
    # 执行对比
    compare_result = await git_service.compare_commits(
        skill_id=skill_id,
        from_commit=compare_data.from_commit,
        to_commit=compare_data.to_commit
    )
    
    if "error" in compare_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=compare_result["error"]
        )
    
    # 构建响应
    diffs = []
    for diff_data in compare_result.get("diffs", []):
        diffs.append(FileDiffResponse(
            file_path=diff_data["file_path"],
            change_type=diff_data["change_type"],
            old_file=diff_data.get("old_file"),
            new_file=diff_data.get("new_file"),
            diff=diff_data.get("diff")
        ))
    
    return VersionCompareResponse(
        from_commit=CommitInfo(**compare_result["from_commit"]),
        to_commit=CommitInfo(**compare_result["to_commit"]),
        files_changed=compare_result["files_changed"],
        diffs=diffs
    )


# ==================== 分支管理 ====================

@router.get("/{skill_id}/branches", response_model=List[BranchResponse])
async def list_branches(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取技能分支列表
    """
    skill = await _get_skill_with_permission(skill_id, current_user, db)
    await _ensure_repo_initialized(skill_id, skill, db)
    
    branches = await git_service.list_branches(skill_id)
    return [BranchResponse(**b) for b in branches]


@router.post("/{skill_id}/branches", status_code=status.HTTP_201_CREATED)
async def create_branch(
    skill_id: int,
    branch_data: BranchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建新分支
    
    - 可从指定提交创建，默认从当前 HEAD 创建
    """
    skill = await _get_skill_with_permission(skill_id, current_user, db)
    await _ensure_repo_initialized(skill_id, skill, db)
    
    result = await git_service.create_branch(
        skill_id=skill_id,
        branch_name=branch_data.branch_name,
        from_commit=branch_data.from_commit
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to create branch")
        )
    
    return {"message": result["message"], "branch_name": branch_data.branch_name}


@router.post("/{skill_id}/branches/switch")
async def switch_branch(
    skill_id: int,
    switch_data: BranchSwitch,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    切换分支
    """
    skill = await _get_skill_with_permission(skill_id, current_user, db)
    await _ensure_repo_initialized(skill_id, skill, db)
    
    result = await git_service.switch_branch(
        skill_id=skill_id,
        branch_name=switch_data.branch_name
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to switch branch")
        )
    
    # 更新技能的分支信息
    skill.git_branch = switch_data.branch_name
    skill.git_commit_hash = result["commit_hash"]
    await db.commit()
    
    return {
        "message": result["message"],
        "branch": switch_data.branch_name,
        "commit_hash": result["commit_hash"]
    }


# ==================== 文件操作 ====================

@router.get("/{skill_id}/versions/{version_id}/files/{file_path:path}")
async def get_file_at_version(
    skill_id: int,
    version_id: str,
    file_path: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定版本的文件内容
    
    - version_id: commit hash
    - file_path: 文件路径
    """
    skill = await _get_skill_with_permission(skill_id, current_user, db)
    await _ensure_repo_initialized(skill_id, skill, db)
    
    content = await git_service.get_file_at_commit(
        skill_id=skill_id,
        commit_hash=version_id,
        file_path=file_path
    )
    
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{file_path}' not found in version '{version_id}'"
        )
    
    return {
        "file_path": file_path,
        "version_id": version_id,
        "content": content
    }
