"""
Skills Hub API - 技能市场发布和管理
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from app.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.skill import Skill
from app.models.published_skill import PublishedSkill, SkillPackage, SkillPermission
from app.schemas.skills_hub import (
    SkillPublishRequest,
    PublishedSkillResponse,
    SkillPackageResponse,
    UploadResponse,
    VersionCreateRequest,
    VersionListResponse,
    PermissionGrantRequest,
    PermissionResponse,
    SkillHubListResponse
)
from app.utils.minio_client import minio_client
from app.config import settings
import slugify
import logging
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

router = APIRouter()


# ============= 辅助函数 =============

async def check_publish_permission(user: User) -> bool:
    """检查用户是否有发布权限"""
    if user.is_superuser:
        return True
    if user.permissions and ("publisher" in user.permissions or "create_skills" in user.permissions):
        return True
    return False


async def check_skill_access(
    db: AsyncSession,
    published_skill_id: int,
    user: User,
    required_permission: str = "read"
) -> PublishedSkill:
    """检查技能访问权限"""
    result = await db.execute(
        select(PublishedSkill).where(PublishedSkill.id == published_skill_id)
    )
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Published skill not found"
        )
    
    # 公开技能任何人都可以读取
    if skill.is_public and required_permission == "read":
        return skill
    
    # 检查权限
    if user.is_superuser:
        return skill
    
    if skill.publisher_id == user.id:
        return skill
    
    # 检查显式权限
    perm_result = await db.execute(
        select(SkillPermission).where(
            and_(
                SkillPermission.published_skill_id == published_skill_id,
                SkillPermission.user_id == user.id
            )
        )
    )
    permission = perm_result.scalar_one_or_none()
    
    if permission:
        perm_levels = {"read": 1, "write": 2, "admin": 3, "owner": 4}
        user_level = perm_levels.get(permission.permission_type, 0)
        required_level = perm_levels.get(required_permission, 0)
        
        if user_level >= required_level:
            return skill
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You don't have permission to access this skill"
    )


async def generate_unique_slug(db: AsyncSession, name: str) -> str:
    """生成唯一的slug"""
    base_slug = slugify.slugify(name)
    slug = base_slug
    counter = 1
    
    while True:
        result = await db.execute(
            select(PublishedSkill).where(PublishedSkill.slug == slug)
        )
        if not result.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug


# ============= API 端点 =============

@router.post("/publish", response_model=PublishedSkillResponse, status_code=status.HTTP_201_CREATED)
async def publish_skill(
    request: SkillPublishRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    发布技能到市场
    
    - 验证用户权限
    - 创建发布记录
    - 状态为pending等待审核
    """
    # 检查发布权限
    if not await check_publish_permission(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Publisher permission required"
        )
    
    # 检查技能是否存在且属于当前用户
    skill_result = await db.execute(
        select(Skill).where(Skill.id == request.skill_id)
    )
    skill = skill_result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    if skill.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only publish your own skills"
        )
    
    # 检查是否已发布
    existing_result = await db.execute(
        select(PublishedSkill).where(PublishedSkill.skill_id == request.skill_id)
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill already published"
        )
    
    # 生成唯一slug
    slug = await generate_unique_slug(db, request.name)
    
    # 创建发布记录
    published_skill = PublishedSkill(
        skill_id=request.skill_id,
        publisher_id=current_user.id,
        name=request.name,
        slug=slug,
        description=request.description,
        version=request.version,
        category=request.category,
        tags=request.tags,
        price=request.price,
        currency=request.currency,
        homepage_url=request.homepage_url,
        repository_url=request.repository_url,
        documentation_url=request.documentation_url,
        license=request.license,
        status="pending",  # 需要审核
        is_public=True
    )
    
    db.add(published_skill)
    await db.commit()
    await db.refresh(published_skill)
    
    logger.info(f"Skill published: {published_skill.id} by user {current_user.id}")
    
    return published_skill


@router.post("/upload", response_model=UploadResponse)
async def upload_skill_package(
    skill_id: int = Query(..., description="已发布技能ID"),
    version: str = Query(..., description="版本号"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传技能包
    
    - 验证文件大小（最大10MB）
    - 验证文件类型
    - 上传到MinIO
    - 创建版本记录
    """
    # 检查技能访问权限（需要write权限）
    published_skill = await check_skill_access(db, skill_id, current_user, "write")
    
    # 检查文件大小
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.MAX_PACKAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size ({settings.MAX_PACKAGE_SIZE} bytes)"
        )
    
    # 检查文件类型
    if not file.filename.endswith(('.tar.gz', '.zip')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .tar.gz or .zip files are allowed"
        )
    
    # 检查版本是否已存在
    existing_result = await db.execute(
        select(SkillPackage).where(
            and_(
                SkillPackage.published_skill_id == skill_id,
                SkillPackage.version == version
            )
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Version {version} already exists"
        )
    
    # 上传到MinIO
    try:
        storage_path, checksum = await minio_client.upload_skill_package(
            skill_id=skill_id,
            version=version,
            file_data=file.file,
            file_size=file_size
        )
    except Exception as e:
        logger.error(f"Failed to upload package: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload package"
        )
    
    # 计算版本号数字
    version_parts = version.split('.')
    version_code = int(version_parts[0]) * 10000 + int(version_parts[1]) * 100 + int(version_parts[2])
    
    # 将之前的版本标记为非最新
    await db.execute(
        select(SkillPackage).where(
            and_(
                SkillPackage.published_skill_id == skill_id,
                SkillPackage.is_latest == True
            )
        )
    )
    # 更新所有is_latest
    old_packages = await db.execute(
        select(SkillPackage).where(SkillPackage.published_skill_id == skill_id)
    )
    for pkg in old_packages.scalars().all():
        pkg.is_latest = False
    
    # 创建技能包记录
    skill_package = SkillPackage(
        published_skill_id=skill_id,
        version=version,
        version_code=version_code,
        storage_path=storage_path,
        file_size=file_size,
        checksum=checksum,
        is_active=True,
        is_latest=True
    )
    
    db.add(skill_package)
    
    # 更新发布技能的版本
    published_skill.version = version
    
    await db.commit()
    await db.refresh(skill_package)
    
    logger.info(f"Skill package uploaded: {skill_package.id} for skill {skill_id}")
    
    return UploadResponse(
        message="Package uploaded successfully",
        package_id=skill_package.id,
        version=version,
        file_size=file_size,
        checksum=checksum
    )


@router.get("/{skill_id}/versions", response_model=VersionListResponse)
async def get_skill_versions(
    skill_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取技能版本列表
    
    - 分页
    - 按版本号排序
    - 包含下载URL
    """
    # 检查技能访问权限
    await check_skill_access(db, skill_id, current_user, "read")
    
    # 查询版本列表
    query = select(SkillPackage).where(
        SkillPackage.published_skill_id == skill_id
    )
    
    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页和排序
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(SkillPackage.version_code.desc())
    
    result = await db.execute(query)
    packages = result.scalars().all()
    
    # 生成下载URL
    items = []
    for pkg in packages:
        download_url = minio_client.get_download_url(skill_id, pkg.version)
        items.append(
            SkillPackageResponse(
                **{c.name: getattr(pkg, c.name) for c in pkg.__table__.columns},
                download_url=download_url
            )
        )
    
    has_more = (offset + len(packages)) < total
    
    return VersionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.post("/{skill_id}/versions", response_model=SkillPackageResponse, status_code=status.HTTP_201_CREATED)
async def publish_new_version(
    skill_id: int,
    request: VersionCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    发布新版本
    
    - 从当前技能文件创建新版本包
    - 上传到MinIO
    - 更新版本信息
    """
    # 检查技能访问权限（需要write权限）
    published_skill = await check_skill_access(db, skill_id, current_user, "write")
    
    # 检查版本是否已存在
    existing_result = await db.execute(
        select(SkillPackage).where(
            and_(
                SkillPackage.published_skill_id == skill_id,
                SkillPackage.version == request.version
            )
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Version {request.version} already exists"
        )
    
    # 获取原始技能
    skill_result = await db.execute(
        select(Skill).where(Skill.id == published_skill.skill_id)
    )
    skill = skill_result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original skill not found"
        )
    
    # TODO: 实际打包逻辑 - 从技能文件创建tar.gz包
    # 这里需要实现从Skill和SkillFile创建压缩包的逻辑
    # 暂时返回一个占位响应
    
    logger.info(f"New version {request.version} published for skill {skill_id}")
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Version creation from skill files not yet implemented"
    )


@router.post("/{skill_id}/permissions", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def grant_permission(
    skill_id: int,
    request: PermissionGrantRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    授予技能权限
    
    - 需要admin或owner权限
    - 可以授予: read, write, admin权限
    - owner权限只能由超级管理员授予
    """
    # 检查权限
    required_perm = "owner" if request.permission_type == "owner" else "admin"
    await check_skill_access(db, skill_id, current_user, required_perm)
    
    # 检查是否已有权限
    existing_result = await db.execute(
        select(SkillPermission).where(
            and_(
                SkillPermission.published_skill_id == skill_id,
                SkillPermission.user_id == request.user_id
            )
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has permission"
        )
    
    # 创建权限记录
    permission = SkillPermission(
        published_skill_id=skill_id,
        user_id=request.user_id,
        permission_type=request.permission_type,
        granted_by=current_user.id,
        expires_at=request.expires_at
    )
    
    db.add(permission)
    await db.commit()
    await db.refresh(permission)
    
    logger.info(f"Permission {request.permission_type} granted to user {request.user_id} for skill {skill_id}")
    
    return permission


@router.get("", response_model=SkillHubListResponse)
async def list_published_skills(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    列出已发布技能（技能市场）
    
    - 支持搜索
    - 支持分类过滤
    - 只显示公开且已审核通过的技能
    """
    # 基础查询 - 只显示公开且已发布的技能
    query = select(PublishedSkill).where(
        and_(
            PublishedSkill.is_public == True,
            PublishedSkill.status == "published"
        )
    )
    
    # 搜索
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                PublishedSkill.name.ilike(search_term),
                PublishedSkill.description.ilike(search_term)
            )
        )
    
    # 分类过滤
    if category:
        query = query.where(PublishedSkill.category == category)
    
    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(PublishedSkill.download_count.desc())
    
    result = await db.execute(query)
    skills = result.scalars().all()
    
    has_more = (offset + len(skills)) < total
    
    return SkillHubListResponse(
        items=skills,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.get("/{skill_id}", response_model=PublishedSkillResponse)
async def get_published_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取已发布技能详情
    """
    skill = await check_skill_access(db, skill_id, current_user, "read")
    return skill
