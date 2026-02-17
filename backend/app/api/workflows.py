"""
工作流路由 - 完整实现
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.database import get_db
from app.dependencies import get_current_user
from app.models.workflow import Workflow
from app.models.user import User
from app.schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse, WorkflowListResponse,
    WorkflowDefinition
)

router = APIRouter()


def validate_workflow_definition(definition: dict) -> bool:
    """
    验证工作流定义结构
    
    Args:
        definition: 工作流定义字典
        
    Returns:
        bool: 是否有效
    """
    if not isinstance(definition, dict):
        return False
    
    nodes = definition.get('nodes', [])
    edges = definition.get('edges', [])
    
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return False
    
    # 验证节点
    node_ids = set()
    for node in nodes:
        if not isinstance(node, dict):
            return False
        node_id = node.get('id')
        if not node_id:
            return False
        node_ids.add(node_id)
        
        # 验证节点类型
        node_type = node.get('type')
        valid_types = ['start', 'end', 'skill', 'condition', 'transform']
        if node_type and node_type not in valid_types:
            return False
    
    # 验证边
    for edge in edges:
        if not isinstance(edge, dict):
            return False
        
        source = edge.get('source')
        target = edge.get('target')
        
        if not source or not target:
            return False
        
        # 检查源节点和目标节点是否存在
        if source not in node_ids or target not in node_ids:
            return False
    
    return True


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    列出工作流（分页、搜索）
    
    - 只返回当前用户的工作流
    - 支持按名称、描述搜索
    - 支持分页
    """
    # 基础查询 - 只显示用户自己的工作流
    query = select(Workflow).where(Workflow.user_id == current_user.id)
    
    # 搜索过滤
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Workflow.name.ilike(search_term),
                Workflow.description.ilike(search_term)
            )
        )
    
    # 状态过滤
    if is_active is not None:
        query = query.where(Workflow.is_active == is_active)
    
    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Workflow.updated_at.desc())
    
    # 执行查询
    result = await db.execute(query)
    workflows = result.scalars().all()
    
    # 计算是否有更多
    has_more = (offset + len(workflows)) < total
    
    return WorkflowListResponse(
        items=workflows,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取工作流详情
    
    - 只能访问自己的工作流
    """
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # 权限检查：只能查看自己的工作流
    if workflow.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this workflow"
        )
    
    return workflow


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_create: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建工作流
    
    - 验证 definition JSON 结构
    - 关联当前用户
    """
    # 获取定义数据（转成 dict 存储）
    definition_dict = workflow_create.definition.model_dump()
    
    # 验证工作流定义
    if not validate_workflow_definition(definition_dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workflow definition structure"
        )
    
    # 转换变量定义
    variables_data = None
    if workflow_create.variables:
        variables_data = [v.model_dump() for v in workflow_create.variables]
    
    # 创建工作流
    workflow = Workflow(
        user_id=current_user.id,
        name=workflow_create.name,
        description=workflow_create.description,
        definition=definition_dict,
        variables=variables_data,
        is_active=workflow_create.is_active
    )
    
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    
    return workflow


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: UUID,
    workflow_update: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新工作流
    
    - 只有工作流所有者可以更新
    - 验证 definition JSON 结构（如果更新）
    """
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # 权限检查
    if workflow.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this workflow"
        )
    
    # 更新字段
    update_data = workflow_update.model_dump(exclude_unset=True)
    
    # 验证并更新 definition
    if 'definition' in update_data and update_data['definition'] is not None:
        definition_dict = update_data['definition']
        if isinstance(definition_dict, dict):
            if not validate_workflow_definition(definition_dict):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid workflow definition structure"
                )
        elif hasattr(definition_dict, 'model_dump'):
            definition_dict = definition_dict.model_dump()
            if not validate_workflow_definition(definition_dict):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid workflow definition structure"
                )
        update_data['definition'] = definition_dict
    
    # 处理变量更新
    if 'variables' in update_data and update_data['variables'] is not None:
        variables_data = update_data['variables']
        if variables_data and hasattr(variables_data[0], 'model_dump'):
            update_data['variables'] = [v.model_dump() for v in variables_data]
    
    for field, value in update_data.items():
        setattr(workflow, field, value)
    
    await db.commit()
    await db.refresh(workflow)
    
    return workflow


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除工作流
    
    - 只有工作流所有者可以删除
    """
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # 权限检查
    if workflow.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this workflow"
        )
    
    await db.delete(workflow)
    await db.commit()
    
    return None
