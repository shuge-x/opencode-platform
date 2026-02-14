"""
技能开发 API - Sprint 6
"""
import os
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.skill import Skill, SkillFile
from app.schemas.skill import (
    SkillCreate, SkillUpdate, SkillResponse, SkillListResponse,
    SkillFileCreate, SkillFileUpdate, SkillFileResponse,
    SkillTemplateResponse
)
from datetime import datetime

router = APIRouter()


# 技能模板
SKILL_TEMPLATES = {
    "basic": {
        "name": "基础技能模板",
        "description": "一个简单的基础技能模板，包含 main.py 和 README.md",
        "file_structure": {
            "main.py": '''"""
技能主文件
"""
def main(params: dict) -> dict:
    """
    技能入口函数

    Args:
        params: 输入参数

    Returns:
        执行结果
    """
    # 在这里编写你的技能逻辑
    result = {
        "message": "Hello, World!",
        "params": params
    }

    return result
''',
            "README.md": '''# 技能名称

## 描述
技能的简要描述

## 参数
- `param1`: 参数1说明
- `param2`: 参数2说明

## 返回值
- `result`: 执行结果

## 示例
```python
result = main({"param1": "value1"})
print(result)
```
''',
            "config.json": '''{
  "name": "My Skill",
  "version": "1.0.0",
  "description": "A basic skill template",
  "author": "Your Name",
  "tags": ["basic", "template"]
}'''
        },
        "skill_type": "basic"
    },
    "api_integration": {
        "name": "API 集成模板",
        "description": "用于调用外部 API 的技能模板",
        "file_structure": {
            "main.py": '''"""
API 集成技能
"""
import requests
import json

def main(params: dict) -> dict:
    """
    调用外部 API

    Args:
        params: 包含 API 配置和参数

    Returns:
        API 响应结果
    """
    api_url = params.get("api_url")
    api_key = params.get("api_key")
    method = params.get("method", "GET")
    headers = params.get("headers", {})
    data = params.get("data")

    # 添加认证头
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        if method == "GET":
            response = requests.get(api_url, headers=headers, params=data)
        else:
            response = requests.post(api_url, headers=headers, json=data)

        return {
            "success": True,
            "status_code": response.status_code,
            "data": response.json()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
''',
            "requirements.txt": "requests>=2.28.0\\n",
            "README.md": "# API 集成技能\\n\\n用于调用外部 API 的技能模板。\\n",
            "config.json": json.dumps({
                "name": "API Integration Skill",
                "version": "1.0.0",
                "description": "A skill template for API integration",
                "author": "Your Name",
                "tags": ["api", "integration"],
                "dependencies": ["requests"]
            }, indent=2)
        },
        "skill_type": "api_integration"
    }
}


@router.get("/templates", response_model=List[SkillTemplateResponse])
async def list_skill_templates():
    """
    列出所有技能模板

    返回可用的技能模板列表，供用户选择
    """
    templates = []
    for template_id, template_data in SKILL_TEMPLATES.items():
        templates.append(
            SkillTemplateResponse(
                name=template_data["name"],
                description=template_data["description"],
                file_structure=template_data["file_structure"],
                skill_type=template_data["skill_type"]
            )
        )

    return templates


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill: SkillCreate,
    template: Optional[str] = Query(None, description="技能模板ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建技能

    - 如果指定模板，会自动创建模板文件
    - 否则创建空技能
    """
    # 创建技能
    db_skill = Skill(
        user_id=current_user.id,
        name=skill.name,
        description=skill.description,
        skill_type=skill.skill_type,
        config=skill.config,
        tags=skill.tags,
        is_public=skill.is_public
    )

    db.add(db_skill)
    await db.commit()
    await db.refresh(db_skill)

    # 如果指定模板，创建模板文件
    if template and template in SKILL_TEMPLATES:
        template_data = SKILL_TEMPLATES[template]
        for filename, content in template_data["file_structure"].items():
            db_file = SkillFile(
                skill_id=db_skill.id,
                filename=filename,
                file_path=filename,
                file_type=_get_file_type(filename),
                content=content
            )
            db.add(db_file)

        await db.commit()
        await db.refresh(db_skill)

    return db_skill


@router.get("", response_model=SkillListResponse)
async def list_skills(
    search: Optional[str] = Query(None, description="搜索技能名称"),
    skill_type: Optional[str] = Query(None, description="技能类型过滤"),
    is_public: Optional[bool] = Query(None, description="公开技能过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    列出技能

    - 支持搜索技能名称
    - 支持按类型过滤
    - 支持分页
    """
    # 基础查询
    query = select(Skill).where(Skill.user_id == current_user.id)

    # 搜索过滤
    if search:
        search_term = f"%{search}%"
        query = query.where(Skill.name.ilike(search_term))

    # 类型过滤
    if skill_type:
        query = query.where(Skill.skill_type == skill_type)

    # 公开过滤
    if is_public is not None:
        query = query.where(Skill.is_public == is_public)

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

    - 包含所有文件内容
    """
    result = await db.execute(
        select(Skill).where(
            Skill.id == skill_id,
            Skill.user_id == current_user.id
        )
    )
    skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )

    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: int,
    skill_update: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新技能信息

    - 只更新提供的字段
    """
    result = await db.execute(
        select(Skill).where(
            Skill.id == skill_id,
            Skill.user_id == current_user.id
        )
    )
    skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )

    # 更新字段
    update_data = skill_update.model_dump(exclude_unset=True)
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

    - 会级联删除所有文件和执行记录
    """
    result = await db.execute(
        select(Skill).where(
            Skill.id == skill_id,
            Skill.user_id == current_user.id
        )
    )
    skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )

    await db.delete(skill)
    await db.commit()

    return None


# 文件管理 API

@router.post("/{skill_id}/files", response_model=SkillFileResponse, status_code=status.HTTP_201_CREATED)
async def create_skill_file(
    skill_id: int,
    file: SkillFileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建技能文件
    """
    # 验证技能存在
    result = await db.execute(
        select(Skill).where(
            Skill.id == skill_id,
            Skill.user_id == current_user.id
        )
    )
    skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )

    # 创建文件
    db_file = SkillFile(
        skill_id=skill_id,
        filename=file.filename,
        file_path=file.file_path,
        file_type=file.file_type,
        content=file.content
    )

    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)

    return db_file


@router.get("/{skill_id}/files", response_model=List[SkillFileResponse])
async def list_skill_files(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    列出技能所有文件
    """
    # 验证技能存在
    result = await db.execute(
        select(Skill).where(
            Skill.id == skill_id,
            Skill.user_id == current_user.id
        )
    )
    skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )

    # 查询文件
    result = await db.execute(
        select(SkillFile).where(SkillFile.skill_id == skill_id)
    )
    files = result.scalars().all()

    return files


@router.get("/{skill_id}/files/{file_id}", response_model=SkillFileResponse)
async def get_skill_file(
    skill_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取技能文件详情
    """
    result = await db.execute(
        select(SkillFile).join(Skill).where(
            SkillFile.id == file_id,
            SkillFile.skill_id == skill_id,
            Skill.user_id == current_user.id
        )
    )
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return file


@router.put("/{skill_id}/files/{file_id}", response_model=SkillFileResponse)
async def update_skill_file(
    skill_id: int,
    file_id: int,
    file_update: SkillFileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新技能文件

    - 用于编辑器保存文件内容
    """
    result = await db.execute(
        select(SkillFile).join(Skill).where(
            SkillFile.id == file_id,
            SkillFile.skill_id == skill_id,
            Skill.user_id == current_user.id
        )
    )
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # 更新字段
    update_data = file_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(file, field, value)

    await db.commit()
    await db.refresh(file)

    return file


@router.delete("/{skill_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill_file(
    skill_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除技能文件
    """
    result = await db.execute(
        select(SkillFile).join(Skill).where(
            SkillFile.id == file_id,
            SkillFile.skill_id == skill_id,
            Skill.user_id == current_user.id
        )
    )
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    await db.delete(file)
    await db.commit()

    return None


def _get_file_type(filename: str) -> str:
    """根据文件名获取文件类型"""
    ext = filename.split(".")[-1].lower()
    type_map = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "md": "markdown",
        "json": "config",
        "yaml": "config",
        "yml": "config",
        "txt": "text"
    }
    return type_map.get(ext, "text")
