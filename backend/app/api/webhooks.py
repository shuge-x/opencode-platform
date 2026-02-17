"""
Webhook 触发 API

处理外部系统通过 Webhook 触发工作流
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging
import json

from app.database import get_db
from app.core.security import get_current_user, get_optional_user
from app.models.user import User
from app.models.workflow import Workflow
from app.models.workflow_execution import (
    WorkflowExecution, ExecutionStatus, TriggerType
)
from app.services.scheduler_service import WebhookTokenManager
from app.schemas.workflow import WorkflowExecutionResponse
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/{token}",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Webhook 触发工作流"
)
async def trigger_workflow_via_webhook(
    token: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    通过 Webhook Token 触发工作流
    
    - 验证 Token 有效性
    - 异步执行工作流
    - 返回执行记录
    
    请求体格式：
    ```json
    {
        "data": { ... },  // 传递给工作流的输入数据
        "options": {      // 可选的执行选项
            "async": true,  // 是否异步执行（默认 true）
            "callback_url": "https://..."  // 执行完成后的回调 URL
        }
    }
    ```
    """
    # 验证 token
    token_manager = WebhookTokenManager()
    workflow_id = await token_manager.validate_token(token)
    
    if not workflow_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired webhook token"
        )
    
    # 获取工作流
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    
    # 检查工作流是否激活
    if not workflow.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow is not active"
        )
    
    # 检查触发配置
    trigger_config = workflow.trigger_config or {}
    if trigger_config.get("type") != TriggerType.WEBHOOK.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow is not configured for webhook triggers"
        )
    
    # 解析请求数据
    try:
        body = await request.json()
    except json.JSONDecodeError:
        body = {}
    
    # 提取输入数据和选项
    input_data = body.get("data", {})
    options = body.get("options", {})
    
    # 添加 webhook 元数据
    input_data["_webhook"] = {
        "token": token[:8] + "..." + token[-4:],  # 隐藏部分 token
        "triggered_at": datetime.utcnow().isoformat(),
        "source_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "content_type": request.headers.get("content-type")
    }
    
    # 添加请求头信息
    headers = dict(request.headers)
    input_data["_headers"] = {k.lower(): v for k, v in headers.items() if k.lower() in [
        "content-type", "x-request-id", "x-webhook-source", "x-signature"
    ]}
    
    # 创建执行记录
    execution = WorkflowExecution(
        workflow_id=workflow_id,
        user_id=workflow.user_id,
        trigger_type=TriggerType.WEBHOOK.value,
        triggered_by=None,  # Webhook 触发没有特定用户
        status=ExecutionStatus.PENDING.value,
        input_data=input_data,
        total_steps=len(workflow.definition.get("nodes", []))
    )
    
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    
    # 异步执行工作流
    async_exec = options.get("async", True)
    
    if async_exec:
        # 使用 Celery 任务执行
        from tasks.workflow_tasks import execute_webhook_workflow
        execute_webhook_workflow.delay(
            workflow_id=workflow_id,
            webhook_data=input_data,
            headers=headers
        )
    else:
        # 同步执行（使用后台任务）
        background_tasks.add_task(
            execute_webhook_sync,
            execution_id=execution.id,
            workflow_id=workflow_id,
            input_data=input_data,
            db_url=settings.DATABASE_URL
        )
    
    logger.info(f"Webhook triggered workflow {workflow_id}, execution_id={execution.id}")
    
    return execution


async def execute_webhook_sync(
    execution_id: int,
    workflow_id: int,
    input_data: Dict[str, Any],
    db_url: str
):
    """
    同步执行 webhook 触发的工作流
    """
    from app.database import AsyncSessionLocal
    from app.services.workflow_executor import WorkflowExecutor
    
    async with AsyncSessionLocal() as db:
        try:
            # 获取工作流和执行记录
            workflow_result = await db.execute(
                select(Workflow).where(Workflow.id == workflow_id)
            )
            workflow = workflow_result.scalar_one_or_none()
            
            execution_result = await db.execute(
                select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
            )
            execution = execution_result.scalar_one_or_none()
            
            if not workflow or not execution:
                logger.error(f"Workflow {workflow_id} or execution {execution_id} not found")
                return
            
            # 更新状态
            execution.status = ExecutionStatus.RUNNING.value
            execution.started_at = datetime.utcnow()
            await db.commit()
            
            # 创建步骤记录
            await _create_step_records(db, execution, workflow.definition)
            
            # 执行工作流
            executor = WorkflowExecutor(db_session=db)
            result = await executor.execute(
                workflow_id=workflow_id,
                execution_id=execution_id,
                input_data=input_data,
                variables_definition=workflow.variables,
                definition=workflow.definition
            )
            
            # 更新执行记录
            execution.status = ExecutionStatus.COMPLETED.value if result["status"] == "completed" else ExecutionStatus.FAILED.value
            execution.finished_at = datetime.utcnow()
            execution.execution_time = (execution.finished_at - execution.started_at).total_seconds()
            execution.output_data = result.get("output", {})
            
            if result["status"] == "failed":
                execution.error_message = result.get("error")
            
            # 更新统计
            context = result.get("context", {})
            stats = context.get("statistics", {})
            execution.completed_steps = stats.get("completed_steps", 0)
            execution.failed_steps = stats.get("failed_steps", 0)
            
            # 更新工作流统计
            workflow.execution_count += 1
            if result["status"] == "completed":
                workflow.success_count += 1
            else:
                workflow.failure_count += 1
            
            await db.commit()
            
            logger.info(f"Webhook execution {execution_id} completed: {result['status']}")
            
        except Exception as e:
            logger.exception(f"Webhook execution failed: {e}")
            
            try:
                execution_result = await db.execute(
                    select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
                )
                execution = execution_result.scalar_one_or_none()
                if execution:
                    execution.status = ExecutionStatus.FAILED.value
                    execution.finished_at = datetime.utcnow()
                    if execution.started_at:
                        execution.execution_time = (execution.finished_at - execution.started_at).total_seconds()
                    execution.error_message = str(e)
                    await db.commit()
            except Exception as update_error:
                logger.exception(f"Failed to update execution status: {update_error}")


async def _create_step_records(db, execution, definition: dict):
    """创建步骤记录"""
    from app.models.workflow_execution import WorkflowExecutionStep, StepStatus
    
    nodes = definition.get("nodes", [])
    
    for node_data in nodes:
        node_id = node_data.get("id")
        node_type = node_data.get("type")
        node_name = node_data.get("data", {}).get("label", "")
        
        step = WorkflowExecutionStep(
            execution_id=execution.id,
            node_id=node_id,
            node_type=node_type,
            node_name=node_name,
            status=StepStatus.PENDING.value
        )
        db.add(step)
    
    await db.commit()


@router.get(
    "/{token}/info",
    summary="获取 Webhook 信息"
)
async def get_webhook_info(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取 Webhook Token 对应的工作流信息
    
    需要登录且是工作流所有者
    """
    # 验证 token
    token_manager = WebhookTokenManager()
    workflow_id = await token_manager.validate_token(token)
    
    if not workflow_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired webhook token"
        )
    
    # 获取工作流
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    
    # 权限检查
    if workflow.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this webhook"
        )
    
    return {
        "workflow_id": workflow_id,
        "workflow_name": workflow.name,
        "workflow_status": workflow.status,
        "is_active": workflow.is_active,
        "webhook_url": f"/api/v1/webhooks/{token}",
        "trigger_config": workflow.trigger_config
    }


@router.post(
    "/{token}/test",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="测试 Webhook"
)
async def test_webhook(
    token: str,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    测试 Webhook 触发
    
    - 需要登录且是工作流所有者
    - 使用测试数据触发工作流
    - 返回执行记录
    """
    # 验证 token
    token_manager = WebhookTokenManager()
    workflow_id = await token_manager.validate_token(token)
    
    if not workflow_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired webhook token"
        )
    
    # 获取工作流
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    
    # 权限检查
    if workflow.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to test this webhook"
        )
    
    # 解析请求数据
    try:
        body = await request.json()
    except json.JSONDecodeError:
        body = {}
    
    # 添加测试标记
    input_data = body.get("data", {})
    input_data["_webhook_test"] = True
    input_data["_triggered_by_user"] = current_user.id
    
    # 创建执行记录
    execution = WorkflowExecution(
        workflow_id=workflow_id,
        user_id=workflow.user_id,
        trigger_type=TriggerType.WEBHOOK.value,
        triggered_by=current_user.id,
        status=ExecutionStatus.PENDING.value,
        input_data=input_data,
        total_steps=len(workflow.definition.get("nodes", []))
    )
    
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    
    # 使用后台任务执行
    background_tasks.add_task(
        execute_webhook_sync,
        execution_id=execution.id,
        workflow_id=workflow_id,
        input_data=input_data,
        db_url=settings.DATABASE_URL
    )
    
    logger.info(f"Webhook test triggered by user {current_user.id}, workflow {workflow_id}")
    
    return execution


# 导出
__all__ = ["router"]
