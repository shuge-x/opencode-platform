"""
Skills Hub API - 技能市场发布和管理
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, BackgroundTasks, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from app.database import get_db
from app.core.security import get_current_user, get_optional_user
from app.models.user import User
from app.models.skill import Skill
from app.models.published_skill import PublishedSkill, SkillPackage, SkillPermission, SkillReview, SkillRating, SkillBookmark
from app.models.category import SkillCategory, SkillCategoryMapping
from app.schemas.skills_hub import (
    SkillPublishRequest,
    PublishedSkillResponse,
    SkillPackageResponse,
    UploadResponse,
    VersionCreateRequest,
    VersionListResponse,
    PermissionGrantRequest,
    PermissionResponse,
    SkillHubListResponse,
    # 搜索相关
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SearchMetadata,
    SearchSuggestion,
    SearchSuggestionsResponse,
    PopularSearchResponse,
    SearchFacetsResponse,
    # 热度统计
    PopularityScoreResponse,
    TopSkillsResponse,
    StatsSummaryResponse,
)
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryListResponse,
    CategoryTreeResponse,
    CategoryStatsResponse,
)
from app.schemas.review import (
    ReviewCreateRequest,
    ReviewUpdateRequest,
    ReviewResponse,
    ReviewListResponse,
    RatingRequest,
    RatingResponse,
    RatingStatsResponse,
    BookmarkCreateRequest,
    BookmarkUpdateRequest,
    BookmarkResponse,
    BookmarkListResponse,
)
from app.utils.minio_client import minio_client
from app.services.search_service import SearchService
from app.services.popularity_service import PopularityService
from app.services.index_sync_service import IndexSyncService
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


# ============= 搜索 API =============
# ✅ 搜索服务已完整实现
# 使用 PostgreSQL 全文搜索作为后端，Redis 缓存热门搜索
# Elasticsearch 支持预留但未启用

@router.post("/search", response_model=SearchResponse)
async def search_skills(
    request: SearchRequest = Body(default=SearchRequest()),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    搜索技能

    **✅ 功能已实现**

    使用 PostgreSQL 全文搜索（tsvector + tsquery）。

    功能特性：
    - ✅ 全文搜索（支持中英文）
    - ✅ 多维度过滤（分类、标签、评分、价格等）
    - ✅ 多种排序方式（热度、评分、下载量、时间、名称）
    - ✅ 搜索高亮显示
    - ✅ 分页支持

    过滤参数：
    - `query`: 搜索关键词
    - `category_id` / `category_slug`: 分类筛选
    - `tags`: 标签筛选（支持多个）
    - `min_rating` / `max_rating`: 评分范围
    - `price_min` / `price_max`: 价格范围
    - `is_free`: 只看免费
    - `is_featured`: 只看精选
    - `publisher_id`: 按发布者筛选

    排序选项：
    - `popularity`: 热度（默认）
    - `rating`: 评分
    - `download_count`: 下载量
    - `created_at`: 发布时间
    - `name`: 名称
    - `price`: 价格
    """
    search_service = SearchService(db)

    items, total, metadata = await search_service.search_skills(
        query=request.query,
        category_id=request.category_id,
        category_slug=request.category_slug,
        tags=request.tags,
        min_rating=request.min_rating,
        max_rating=request.max_rating,
        price_min=request.price_min,
        price_max=request.price_max,
        is_free=request.is_free,
        is_featured=request.is_featured,
        publisher_id=request.publisher_id,
        sort_by=request.sort_by,
        sort_order=request.sort_order,
        page=request.page,
        page_size=request.page_size,
        include_highlights=True
    )

    # 记录搜索
    if request.query:
        await search_service.record_search(request.query, total)

    return SearchResponse(
        items=[SearchResultItem(**item) for item in items],
        total=total,
        metadata=SearchMetadata(**metadata)
    )


@router.get("/search/suggestions", response_model=SearchSuggestionsResponse)
async def get_search_suggestions(
    query: str = Query(..., min_length=2, description="搜索前缀"),
    limit: int = Query(10, ge=1, le=20, description="返回数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取搜索建议

    **✅ 功能已实现**

    基于技能名称和标签提供自动补全建议。

    功能特性：
    - ✅ 技能名称前缀匹配
    - ✅ 标签前缀匹配
    - ✅ 按下载量排序
    - ✅ Redis 缓存（5分钟过期）
    """
    search_service = SearchService(db)
    suggestions = await search_service.get_search_suggestions(query, limit)

    return SearchSuggestionsResponse(
        suggestions=[SearchSuggestion(**s) for s in suggestions],
        query=query
    )


@router.get("/search/popular", response_model=PopularSearchResponse)
async def get_popular_searches(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取热门搜索

    **✅ 功能已实现**

    返回下载量最高的技能，作为热门搜索推荐。

    功能特性：
    - ✅ 基于下载量排行
    - ✅ Redis 缓存（1小时过期）
    """
    search_service = SearchService(db)
    items = await search_service.get_popular_searches(limit)

    return PopularSearchResponse(
        items=items,
        updated_at=datetime.utcnow().isoformat()
    )


@router.get("/search/facets", response_model=SearchFacetsResponse)
async def get_search_facets(
    db: AsyncSession = Depends(get_db)
):
    """
    获取搜索面（筛选器数据）

    **✅ 功能已实现**

    返回各维度的统计数据，用于构建筛选器 UI。

    功能特性：
    - ✅ 分类统计（包含技能数量）
    - ✅ 价格范围（最小/最大）
    - ✅ 评分分布
    - ✅ Redis 缓存（1小时过期）
    """
    search_service = SearchService(db)
    facets = await search_service.get_facets()

    return SearchFacetsResponse(**facets)


# ============= 分类管理 API =============

@router.get("/categories", response_model=CategoryListResponse)
async def list_categories(
    include_inactive: bool = Query(False, description="包含未激活分类"),
    parent_id: Optional[int] = Query(None, description="父分类ID，为空则返回顶级分类"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取分类列表

    - 支持层级筛选
    - 按排序顺序返回
    """
    query = select(SkillCategory)

    if not include_inactive:
        query = query.where(SkillCategory.is_active == True)

    if parent_id is not None:
        query = query.where(SkillCategory.parent_id == parent_id)
    else:
        query = query.where(SkillCategory.parent_id == None)

    query = query.order_by(SkillCategory.sort_order.asc(), SkillCategory.name.asc())

    result = await db.execute(query)
    categories = result.scalars().all()

    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    return CategoryListResponse(
        items=[CategoryResponse.model_validate(cat) for cat in categories],
        total=total
    )


@router.get("/categories/tree", response_model=List[CategoryTreeResponse])
async def get_category_tree(
    include_inactive: bool = Query(False, description="包含未激活分类"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取分类树

    - 返回完整的层级结构
    - 包含子分类
    """
    query = select(SkillCategory)

    if not include_inactive:
        query = query.where(SkillCategory.is_active == True)

    query = query.order_by(SkillCategory.sort_order.asc())

    result = await db.execute(query)
    all_categories = result.scalars().all()

    # 构建树结构
    def build_tree(parent_id=None):
        children = []
        for cat in all_categories:
            if cat.parent_id == parent_id:
                children.append(CategoryTreeResponse(
                    id=cat.id,
                    name=cat.name,
                    slug=cat.slug,
                    description=cat.description,
                    parent_id=cat.parent_id,
                    icon=cat.icon,
                    color=cat.color,
                    sort_order=cat.sort_order,
                    is_active=cat.is_active,
                    skill_count=cat.skill_count,
                    created_at=cat.created_at,
                    updated_at=cat.updated_at,
                    children=build_tree(cat.id)
                ))
        return children

    return build_tree()


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取分类详情
    """
    result = await db.execute(
        select(SkillCategory).where(SkillCategory.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    return CategoryResponse.model_validate(category)


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    request: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建分类（管理员）

    - 需要管理员权限
    - 自动生成 slug
    """
    # 检查管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required"
        )

    # 生成 slug
    slug = slugify.slugify(request.name) if not request.slug else request.slug

    # 检查 slug 是否已存在
    existing = await db.execute(
        select(SkillCategory).where(SkillCategory.slug == slug)
    )
    if existing.scalar_one_or_none():
        counter = 1
        while True:
            new_slug = f"{slug}-{counter}"
            existing = await db.execute(
                select(SkillCategory).where(SkillCategory.slug == new_slug)
            )
            if not existing.scalar_one_or_none():
                slug = new_slug
                break
            counter += 1

    # 创建分类
    category = SkillCategory(
        name=request.name,
        slug=slug,
        description=request.description,
        parent_id=request.parent_id,
        icon=request.icon,
        color=request.color,
        sort_order=request.sort_order
    )

    db.add(category)
    await db.commit()
    await db.refresh(category)

    logger.info(f"Category created: {category.id} by user {current_user.id}")

    return CategoryResponse.model_validate(category)


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    request: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新分类（管理员）
    """
    # 检查管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required"
        )

    # 获取分类
    result = await db.execute(
        select(SkillCategory).where(SkillCategory.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # 更新字段
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)

    await db.commit()
    await db.refresh(category)

    logger.info(f"Category updated: {category_id} by user {current_user.id}")

    return CategoryResponse.model_validate(category)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除分类（管理员）

    - 如果有子分类则不能删除
    """
    # 检查管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required"
        )

    # 检查是否有子分类
    children = await db.execute(
        select(func.count()).where(SkillCategory.parent_id == category_id)
    )
    if children.scalar() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with children"
        )

    # 删除分类
    result = await db.execute(
        select(SkillCategory).where(SkillCategory.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    await db.delete(category)
    await db.commit()

    logger.info(f"Category deleted: {category_id} by user {current_user.id}")


@router.get("/categories/{category_id}/stats", response_model=CategoryStatsResponse)
async def get_category_stats(
    category_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取分类统计

    - 技能数量
    - 下载量
    - 平均评分
    """
    # 获取分类
    result = await db.execute(
        select(SkillCategory).where(SkillCategory.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # 统计该分类下的技能
    stats = await db.execute(
        select(
            func.count(SkillCategoryMapping.id).label("skill_count"),
            func.coalesce(func.sum(PublishedSkill.download_count), 0).label("download_count"),
            func.coalesce(func.avg(PublishedSkill.rating), 0).label("avg_rating")
        )
        .select_from(SkillCategoryMapping)
        .join(PublishedSkill, SkillCategoryMapping.published_skill_id == PublishedSkill.id)
        .where(
            and_(
                SkillCategoryMapping.category_id == category_id,
                PublishedSkill.status == "published"
            )
        )
    )
    row = stats.first()

    return CategoryStatsResponse(
        category_id=category_id,
        category_name=category.name,
        skill_count=row.skill_count or 0,
        download_count=row.download_count or 0,
        avg_rating=float(row.avg_rating or 0)
    )


# ============= 热度统计 API =============

@router.get("/stats/summary", response_model=StatsSummaryResponse)
async def get_stats_summary(
    db: AsyncSession = Depends(get_db)
):
    """
    获取统计摘要

    - 总技能数
    - 总下载量
    - 平均下载量
    - 平均评分
    """
    popularity_service = PopularityService(db)
    stats = await popularity_service.get_stats_summary()

    return StatsSummaryResponse(**stats)


@router.get("/stats/top", response_model=TopSkillsResponse)
async def get_top_skills(
    limit: int = Query(100, ge=1, le=500, description="返回数量"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取热门技能排行

    - 基于热度分数
    - 支持分类筛选
    """
    popularity_service = PopularityService(db)
    items = await popularity_service.get_top_skills_by_popularity(limit, category_id)

    return TopSkillsResponse(
        items=items,
        category_id=category_id,
        updated_at=datetime.utcnow().isoformat()
    )


@router.get("/{skill_id}/popularity", response_model=PopularityScoreResponse)
async def get_skill_popularity(
    skill_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取技能热度分数

    - 返回各维度分数
    - 包含总热度分数
    """
    popularity_service = PopularityService(db)

    # 获取技能
    result = await db.execute(
        select(PublishedSkill).where(PublishedSkill.id == skill_id)
    )
    skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )

    score = await popularity_service.calculate_popularity_score(
        skill_id=skill.id,
        download_count=skill.download_count,
        install_count=skill.install_count,
        rating=skill.rating,
        rating_count=skill.rating_count,
        published_at=skill.published_at,
        updated_at=skill.updated_at
    )

    # 获取各维度分数（简化版）
    components = {
        "download": skill.download_count,
        "install": skill.install_count,
        "rating": float(skill.rating or 0),
        "rating_count": skill.rating_count
    }

    return PopularityScoreResponse(
        skill_id=skill_id,
        score=score,
        components=components
    )


@router.post("/{skill_id}/download", status_code=status.HTTP_204_NO_CONTENT)
async def record_download(
    skill_id: int,
    package_id: Optional[int] = Query(None, description="包ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    记录下载（用于统计）

    - 更新下载计数
    - 异步更新热度
    """
    popularity_service = PopularityService(db)
    await popularity_service.update_stats_on_download(skill_id, package_id)


@router.post("/{skill_id}/install", status_code=status.HTTP_204_NO_CONTENT)
async def record_install(
    skill_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    记录安装（用于统计）

    - 更新安装计数
    """
    popularity_service = PopularityService(db)
    await popularity_service.update_stats_on_install(skill_id)


# ============= 索引管理 API（管理员） =============

@router.post("/admin/index/rebuild", status_code=status.HTTP_202_ACCEPTED)
async def rebuild_search_index(
    clear_existing: bool = Query(True, description="清除现有索引"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    重建搜索索引（管理员）

    - 清除现有缓存
    - 重新索引所有技能
    """
    # 检查管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required"
        )

    index_service = IndexSyncService(db)

    # 在后台执行
    stats = await index_service.rebuild_index(clear_existing=clear_existing)

    logger.info(f"Search index rebuilt by user {current_user.id}: {stats}")

    return {"message": "Index rebuild completed", "stats": stats}


@router.post("/admin/popularity/update", status_code=status.HTTP_202_ACCEPTED)
async def update_popularity_scores(
    skill_ids: Optional[List[int]] = Body(None, description="指定技能ID，为空则更新所有"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新热度分数（管理员）

    - 批量计算热度
    - 更新缓存
    """
    # 检查管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required"
        )

    popularity_service = PopularityService(db)
    updated_count = await popularity_service.batch_update_popularity_scores(skill_ids)

    logger.info(f"Popularity scores updated by user {current_user.id}: {updated_count} skills")

    return {"message": "Popularity scores updated", "updated_count": updated_count}
