"""
技能路由 - 完整实现
"""
from typing import Optional
import slugify
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.database import get_db
from app.core.security import get_current_user
from app.models.skill import Skill
from app.models.user import User
from app.schemas.skill import SkillCreate, SkillUpdate, SkillResponse, SkillListResponse

router = APIRouter()


@router.get("", response_model=SkillListResponse)
async def list_skills(
    search: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类过滤"),
    tags: Optional[str] = Query(None, description="标签过滤（逗号分隔）"),
    is_public: Optional[bool] = Query(True, description="只显示公开技能"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    搜索技能（分页、过滤）
    
    - 支持按名称、描述搜索
    - 支持按分类、标签过滤
    - 支持分页
    """
    # 基础查询 - 显示公开的或用户自己的技能
    query = select(Skill).where(
        or_(
            Skill.is_public == True,
            Skill.user_id == current_user.id
        )
    )
    
    # 搜索过滤
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Skill.name.ilike(search_term),
                Skill.description.ilike(search_term),
                Skill.prompt_template.ilike(search_term)
            )
        )
    
    # 分类过滤
    if category:
        query = query.where(Skill.category == category)
    
    # 标签过滤
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        # 简单的标签包含检查（JSON数组）
        for tag in tag_list:
            query = query.where(Skill.tags.contains([tag]))
    
    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Skill.created_at.desc())
    
    # 执行查询
    result = await db.execute(query)
    skills = result.scalars().all()
    
    # 计算是否有更多
    has_more = (offset + len(skills)) < total
    
    return SkillListResponse(
        items=skills,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取技能详情
    """
    result = await db.execute(
        select(Skill).where(Skill.id == skill_id)
    )
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    # 权限检查：只能查看公开的或自己的技能
    if not skill.is_public and skill.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this skill"
        )
    
    return skill


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_create: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建技能（需要developer权限）
    
    - 自动生成唯一slug
    - 验证用户是否有developer权限
    """
    # 检查用户权限
    if not current_user.permissions:
        current_user.permissions = []
    
    has_developer_permission = (
        "developer" in current_user.permissions or
        "create_skills" in current_user.permissions or
        current_user.is_superuser
    )
    
    if not has_developer_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Developer permission required to create skills"
        )
    
    # 生成唯一slug
    base_slug = slugify.slugify(skill_create.name)
    slug = base_slug
    counter = 1
    
    while True:
        # 检查slug是否已存在
        existing = await db.execute(
            select(Skill).where(Skill.slug == slug)
        )
        if not existing.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # 创建技能
    skill = Skill(
        user_id=current_user.id,
        name=skill_create.name,
        slug=slug,
        description=skill_create.description,
        category=skill_create.category,
        prompt_template=skill_create.prompt_template,
        config=skill_create.config or {},
        tags=skill_create.tags or [],
        is_public=skill_create.is_public
    )
    
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    
    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: int,
    skill_update: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新技能
    
    - 只有技能所有者或管理员可以更新
    """
    result = await db.execute(
        select(Skill).where(Skill.id == skill_id)
    )
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    # 权限检查
    if skill.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this skill"
        )
    
    # 更新字段
    update_data = skill_update.model_dump(exclude_unset=True)
    
    # 如果更新名称，需要更新slug
    if "name" in update_data:
        base_slug = slugify.slugify(update_data["name"])
        slug = base_slug
        counter = 1
        
        while True:
            existing = await db.execute(
                select(Skill).where(
                    Skill.slug == slug,
                    Skill.id != skill_id
                )
            )
            if not existing.scalar_one_or_none():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        skill.slug = slug
    
    for field, value in update_data.items():
        setattr(skill, field, value)
    
    await db.commit()
    await db.refresh(skill)
    
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除技能
    
    - 只有技能所有者或管理员可以删除
    """
    result = await db.execute(
        select(Skill).where(Skill.id == skill_id)
    )
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    # 权限检查
    if skill.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this skill"
        )
    
    await db.delete(skill)
    await db.commit()
    
    return None


@router.post("/{skill_id}/install")
async def install_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    安装技能
    
    - 增加使用计数
    - 返回技能配置供前端使用
    """
    result = await db.execute(
        select(Skill).where(Skill.id == skill_id)
    )
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    # 检查权限
    if not skill.is_public and skill.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to install this skill"
        )
    
    # 增加使用计数
    skill.use_count += 1
    await db.commit()
    
    # TODO: 实际安装逻辑（可以复制到用户的技能列表、发送到CLI等）
    
    return {
        "message": "Skill installed successfully",
        "skill_id": skill_id,
        "skill_slug": skill.slug,
        "skill_name": skill.name,
        "prompt_template": skill.prompt_template,
        "config": skill.config
    }
