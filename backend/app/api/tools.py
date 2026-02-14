"""
工具调用路由 - 工具可视化与权限管理
"""
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.tool import ToolCall, ToolExecutionLog, ToolStatus
from app.schemas.tool import (
    ToolCallCreate, ToolCallResponse, ToolCallListResponse,
    ToolExecutionLogCreate, ToolExecutionLogResponse, PermissionDecision
)
from datetime import datetime

router = APIRouter()


@router.post("", response_model=ToolCallResponse, status_code=status.HTTP_201_CREATED)
async def create_tool_call(
    tool_call: ToolCallCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建工具调用记录

    - 记录工具名称、参数、状态
    - 如果需要权限，标记为 permission_required
    """
    # 创建工具调用记录
    db_tool_call = ToolCall(
        session_id=tool_call.session_id,
        message_id=tool_call.message_id,
        tool_name=tool_call.tool_name,
        tool_description=tool_call.tool_description,
        parameters=json.dumps(tool_call.parameters) if tool_call.parameters else None,
        status=ToolStatus.PENDING,
        requires_permission=tool_call.requires_permission,
        permission_reason=tool_call.permission_reason
    )

    if tool_call.requires_permission:
        db_tool_call.status = ToolStatus.PERMISSION_REQUIRED

    db.add(db_tool_call)
    await db.commit()
    await db.refresh(db_tool_call)

    return db_tool_call


@router.get("", response_model=ToolCallListResponse)
async def list_tool_calls(
    session_id: Optional[int] = Query(None, description="会话ID过滤"),
    status: Optional[ToolStatus] = Query(None, description="状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    列出工具调用记录

    - 支持按会话过滤
    - 支持按状态过滤
    - 支持分页
    """
    # 基础查询
    query = select(ToolCall)

    # 会话过滤
    if session_id:
        query = query.where(ToolCall.session_id == session_id)

    # 状态过滤
    if status:
        query = query.where(ToolCall.status == status)

    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(ToolCall.created_at.desc())

    # 执行查询
    result = await db.execute(query)
    tool_calls = result.scalars().all()

    # 计算是否有更多
    has_more = (offset + len(tool_calls)) < total

    return ToolCallListResponse(
        items=tool_calls,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.get("/{tool_call_id}", response_model=ToolCallResponse)
async def get_tool_call(
    tool_call_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取工具调用详情

    - 包含执行日志
    """
    # 查询工具调用
    result = await db.execute(
        select(ToolCall).where(ToolCall.id == tool_call_id)
    )
    tool_call = result.scalar_one_or_none()

    if not tool_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool call not found"
        )

    return tool_call


@router.post("/{tool_call_id}/execute", response_model=ToolCallResponse)
async def execute_tool_call(
    tool_call_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    执行工具调用

    - 更新状态为 running
    - 后台执行工具
    - 记录执行日志
    """
    # 查询工具调用
    result = await db.execute(
        select(ToolCall).where(ToolCall.id == tool_call_id)
    )
    tool_call = result.scalar_one_or_none()

    if not tool_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool call not found"
        )

    # 检查权限
    if tool_call.status == ToolStatus.PERMISSION_REQUIRED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission required. Please grant permission first."
        )

    # 更新状态
    tool_call.status = ToolStatus.RUNNING
    tool_call.started_at = datetime.utcnow()
    await db.commit()
    await db.refresh(tool_call)

    # TODO: 后台执行工具
    # background_tasks.add_task(execute_tool_background, tool_call_id)

    return tool_call


@router.post("/{tool_call_id}/permission", response_model=ToolCallResponse)
async def grant_permission(
    tool_call_id: int,
    decision: PermissionDecision,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    权限确认

    - granted=True: 允许执行
    - granted=False: 拒绝执行
    """
    # 查询工具调用
    result = await db.execute(
        select(ToolCall).where(ToolCall.id == tool_call_id)
    )
    tool_call = result.scalar_one_or_none()

    if not tool_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool call not found"
        )

    # 检查状态
    if tool_call.status != ToolStatus.PERMISSION_REQUIRED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tool call does not require permission"
        )

    # 更新权限状态
    tool_call.permission_granted = decision.granted
    tool_call.permission_reason = decision.reason

    if decision.granted:
        tool_call.status = ToolStatus.PENDING
    else:
        tool_call.status = ToolStatus.PERMISSION_DENIED

    await db.commit()
    await db.refresh(tool_call)

    # 记录日志
    log = ToolExecutionLog(
        tool_call_id=tool_call_id,
        log_level="INFO",
        message=f"Permission {'granted' if decision.granted else 'denied'} by user"
    )
    db.add(log)
    await db.commit()

    return tool_call


@router.post("/{tool_call_id}/logs", response_model=ToolExecutionLogResponse, status_code=status.HTTP_201_CREATED)
async def add_execution_log(
    tool_call_id: int,
    log: ToolExecutionLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    添加执行日志

    - 用于记录工具执行过程中的详细信息
    """
    # 验证工具调用存在
    result = await db.execute(
        select(ToolCall).where(ToolCall.id == tool_call_id)
    )
    tool_call = result.scalar_one_or_none()

    if not tool_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool call not found"
        )

    # 创建日志
    db_log = ToolExecutionLog(
        tool_call_id=tool_call_id,
        log_level=log.log_level,
        message=log.message,
        metadata=json.dumps(log.metadata) if log.metadata else None
    )

    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)

    return db_log


@router.get("/{tool_call_id}/logs", response_model=list[ToolExecutionLogResponse])
async def get_execution_logs(
    tool_call_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取执行日志

    - 按时间倒序返回
    """
    # 验证工具调用存在
    result = await db.execute(
        select(ToolCall).where(ToolCall.id == tool_call_id)
    )
    tool_call = result.scalar_one_or_none()

    if not tool_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool call not found"
        )

    # 查询日志
    result = await db.execute(
        select(ToolExecutionLog)
        .where(ToolExecutionLog.tool_call_id == tool_call_id)
        .order_by(ToolExecutionLog.created_at.asc())
    )
    logs = result.scalars().all()

    return logs
