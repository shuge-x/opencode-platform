"""
会话路由
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import logging

from app.database import get_db
from app.core.security import get_current_user
from app.models.session import Session
from app.models.user import User
from app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    Message as MessageSchema,
    ChatRequest,
    ChatResponse
)
from tasks.agent_tasks import execute_agent_task

router = APIRouter()
logger = logging.getLogger(__name__)


def submit_celery_task(task_func, *args, **kwargs):
    """
    安全提交 Celery 任务，包含错误处理
    
    Args:
        task_func: Celery 任务函数
        *args, **kwargs: 任务参数
        
    Returns:
        AsyncResult: 任务结果对象
        
    Raises:
        HTTPException: 任务提交失败时
    """
    try:
        task = task_func.delay(*args, **kwargs)
        logger.info(f"Celery task submitted: {task.id}")
        return task
    except Exception as e:
        logger.error(f"Failed to submit Celery task: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task processing service unavailable. Please try again later."
        )


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_create: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建新会话
    """
    # 创建会话
    session = Session(
        user_id=current_user.id,
        messages=[],
        context=session_create.context or {}
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return session


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户会话列表
    """
    # 查询用户的会话
    result = await db.execute(
        select(Session)
        .where(Session.user_id == current_user.id)
        .order_by(desc(Session.updated_at))
        .offset(skip)
        .limit(limit)
    )
    sessions = result.scalars().all()

    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取会话详情
    """
    # 查询会话
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return session


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    session_update: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新会话
    """
    # 查询会话
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # 更新会话
    if session_update.context:
        session.context = session_update.context

    session.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(session)

    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除会话
    """
    # 查询会话
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # 删除会话
    await db.delete(session)
    await db.commit()

    return None


@router.post("/{session_id}/chat", response_model=ChatResponse)
async def send_message(
    session_id: str,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    发送消息（提交Celery任务）

    注意：推荐使用WebSocket进行实时对话
    """
    # 查询会话
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # 提交Celery任务（带错误处理）
    task = submit_celery_task(
        execute_agent_task,
        prompt=chat_request.message,
        session_id=session_id,
        user_id=current_user.id
    )

    return ChatResponse(
        task_id=task.id,
        status="pending",
        session_id=session_id
    )
