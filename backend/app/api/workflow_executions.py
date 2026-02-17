"""
工作流执行 API

提供工作流执行、查询、取消等功能
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, desc
from datetime import datetime
import logging
import traceback

from app.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.workflow import Workflow
from app.models.workflow_execution import (
    WorkflowExecution, WorkflowExecutionStep, ExecutionLog,
    ExecutionStatus, StepStatus, TriggerType
)
from app.schemas.workflow import (
    WorkflowExecuteRequest,
    WorkflowExecutionResponse,
    WorkflowExecutionDetailResponse,
    WorkflowExecutionStepResponse,
    WorkflowExecutionListResponse,
    ExecutionCancelRequest,
    ExecutionCancelResponse,
    ExecutionLogResponse,
    ExecutionLogQuery
)
from app.services.workflow_executor import WorkflowExecutor, ExecutionCancelledError
from app.services.execution_context import ExecutionContextManager

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ 执行工作流 ============

@router.post(
    "/workflows/{workflow_id}/execute",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="执行工作流"
)
async def execute_workflow(
    workflow_id: int,
    request: WorkflowExecuteRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    执行指定的工作流
    
    - 创建执行记录
    - 在后台执行工作流
    - 返回执行记录 ID
    """
    # 检查工作流是否存在
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
            detail="You don't have permission to execute this workflow"
        )
    
    # 检查工作流是否激活
    if not workflow.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow is not active"
        )
    
    # 创建执行记录
    execution = WorkflowExecution(
        workflow_id=workflow_id,
        user_id=current_user.id,
        trigger_type=request.trigger_type.value,
        triggered_by=current_user.id,
        status=ExecutionStatus.PENDING.value,
        input_data=request.input_data,
        total_steps=len(workflow.definition.get("nodes", []))
    )
    
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    
    # 在后台执行工作流
    background_tasks.add_task(
        execute_workflow_background,
        execution_id=execution.id,
        workflow_id=workflow_id,
        definition=workflow.definition,
        input_data=request.input_data,
        variables_definition=workflow.variables
    )
    
    logger.info(f"Workflow execution started: execution_id={execution.id}, workflow_id={workflow_id}")
    
    return execution


async def execute_workflow_background(
    execution_id: int,
    workflow_id: int,
    definition: dict,
    input_data: dict,
    variables_definition: list
):
    """
    后台执行工作流
    
    注意：这个函数在后台任务中运行，需要创建新的数据库会话
    """
    from app.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            # 更新状态为运行中
            result = await db.execute(
                select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
            )
            execution = result.scalar_one_or_none()
            
            if not execution:
                logger.error(f"Execution {execution_id} not found")
                return
            
            execution.status = ExecutionStatus.RUNNING.value
            execution.started_at = datetime.utcnow()
            await db.commit()
            
            # 创建执行器并执行
            executor = WorkflowExecutor(db_session=db)
            
            # 创建步骤记录
            await _create_step_records(db, execution, definition)
            
            # 执行工作流
            result = await executor.execute(
                workflow_id=workflow_id,
                execution_id=execution_id,
                input_data=input_data,
                variables_definition=variables_definition,
                definition=definition
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
            
            # 保存日志
            await _save_execution_logs(db, execution_id, context.get("logs", []))
            
            # 更新工作流统计
            workflow_result = await db.execute(
                select(Workflow).where(Workflow.id == workflow_id)
            )
            workflow = workflow_result.scalar_one_or_none()
            if workflow:
                workflow.execution_count += 1
                if result["status"] == "completed":
                    workflow.success_count += 1
                else:
                    workflow.failure_count += 1
            
            await db.commit()
            
            logger.info(f"Workflow execution completed: execution_id={execution_id}, status={result['status']}")
            
        except Exception as e:
            logger.exception(f"Workflow execution failed: execution_id={execution_id}, error={e}")
            
            # 更新错误状态
            try:
                result = await db.execute(
                    select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
                )
                execution = result.scalar_one_or_none()
                if execution:
                    execution.status = ExecutionStatus.FAILED.value
                    execution.finished_at = datetime.utcnow()
                    if execution.started_at:
                        execution.execution_time = (execution.finished_at - execution.started_at).total_seconds()
                    execution.error_message = str(e)
                    execution.error_stack = traceback.format_exc()
                    await db.commit()
            except Exception as update_error:
                logger.exception(f"Failed to update execution status: {update_error}")


async def _create_step_records(
    db: AsyncSession,
    execution: WorkflowExecution,
    definition: dict
):
    """创建步骤记录"""
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


async def _save_execution_logs(
    db: AsyncSession,
    execution_id: int,
    logs: list
):
    """保存执行日志"""
    for log_data in logs:
        log = ExecutionLog(
            execution_id=execution_id,
            level=log_data.get("level", "INFO"),
            message=log_data.get("message", ""),
            metadata=log_data.get("metadata", {})
        )
        db.add(log)
    
    await db.commit()


# ============ 查询执行记录 ============

@router.get(
    "/workflows/{workflow_id}/executions",
    response_model=WorkflowExecutionListResponse,
    summary="获取工作流执行历史"
)
async def list_workflow_executions(
    workflow_id: int,
    status_filter: Optional[str] = Query(None, alias="status", description="状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定工作流的执行历史
    """
    # 检查工作流权限
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    
    if workflow.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this workflow's executions"
        )
    
    # 构建查询
    query = select(WorkflowExecution).where(
        WorkflowExecution.workflow_id == workflow_id
    )
    
    if status_filter:
        query = query.where(WorkflowExecution.status == status_filter)
    
    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(WorkflowExecution.created_at.desc())
    
    result = await db.execute(query)
    executions = result.scalars().all()
    
    has_more = (offset + len(executions)) < total
    
    return WorkflowExecutionListResponse(
        items=executions,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.get(
    "/executions/{execution_id}",
    response_model=WorkflowExecutionDetailResponse,
    summary="获取执行详情"
)
async def get_execution_detail(
    execution_id: int,
    include_logs: bool = Query(False, description="是否包含日志"),
    log_limit: int = Query(100, ge=1, le=1000, description="日志数量限制"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取执行详情，包括步骤信息
    """
    result = await db.execute(
        select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )
    
    # 权限检查
    if execution.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this execution"
        )
    
    # 获取步骤
    steps_result = await db.execute(
        select(WorkflowExecutionStep)
        .where(WorkflowExecutionStep.execution_id == execution_id)
        .order_by(WorkflowExecutionStep.created_at)
    )
    steps = steps_result.scalars().all()
    
    # 获取日志
    logs = []
    if include_logs:
        logs_result = await db.execute(
            select(ExecutionLog)
            .where(ExecutionLog.execution_id == execution_id)
            .order_by(ExecutionLog.created_at)
            .limit(log_limit)
        )
        logs = logs_result.scalars().all()
    
    return WorkflowExecutionDetailResponse(
        id=execution.id,
        workflow_id=execution.workflow_id,
        user_id=execution.user_id,
        trigger_type=execution.trigger_type,
        status=execution.status,
        input_data=execution.input_data or {},
        output_data=execution.output_data or {},
        error_message=execution.error_message,
        error_node_id=execution.error_node_id,
        total_steps=execution.total_steps,
        completed_steps=execution.completed_steps,
        failed_steps=execution.failed_steps,
        started_at=execution.started_at,
        finished_at=execution.finished_at,
        execution_time=execution.execution_time,
        created_at=execution.created_at,
        context_data=execution.context_data or {},
        steps=[WorkflowExecutionStepResponse.model_validate(s) for s in steps],
        logs=[ExecutionLogResponse.model_validate(l) for l in logs]
    )


# ============ 取消执行 ============

@router.post(
    "/executions/{execution_id}/cancel",
    response_model=ExecutionCancelResponse,
    summary="取消执行"
)
async def cancel_execution(
    execution_id: int,
    request: ExecutionCancelRequest = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    取消正在执行的工作流
    
    - 只有执行的所有者或管理员可以取消
    - 只能取消正在运行或等待中的执行
    """
    result = await db.execute(
        select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )
    
    # 权限检查
    if execution.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to cancel this execution"
        )
    
    # 检查状态
    if execution.status not in [ExecutionStatus.PENDING.value, ExecutionStatus.RUNNING.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel execution with status: {execution.status}"
        )
    
    # 尝试取消
    reason = request.reason if request else "Cancelled by user"
    cancelled = WorkflowExecutor.cancel_execution(execution_id, reason)
    
    if cancelled:
        # 更新数据库
        execution.status = ExecutionStatus.CANCELLED.value
        execution.cancelled_at = datetime.utcnow()
        execution.cancelled_by = current_user.id
        execution.cancel_reason = reason
        execution.finished_at = datetime.utcnow()
        
        if execution.started_at:
            execution.execution_time = (execution.finished_at - execution.started_at).total_seconds()
        
        await db.commit()
        
        return ExecutionCancelResponse(
            id=execution_id,
            status=ExecutionStatus.CANCELLED.value,
            message="Execution cancelled successfully",
            cancelled_at=execution.cancelled_at
        )
    else:
        # 如果执行器中没有上下文，直接更新状态
        execution.status = ExecutionStatus.CANCELLED.value
        execution.cancelled_at = datetime.utcnow()
        execution.cancelled_by = current_user.id
        execution.cancel_reason = reason
        execution.finished_at = datetime.utcnow()
        
        await db.commit()
        
        return ExecutionCancelResponse(
            id=execution_id,
            status=ExecutionStatus.CANCELLED.value,
            message="Execution marked as cancelled",
            cancelled_at=execution.cancelled_at
        )


# ============ 执行日志 ============

@router.get(
    "/executions/{execution_id}/logs",
    response_model=list[ExecutionLogResponse],
    summary="获取执行日志"
)
async def get_execution_logs(
    execution_id: int,
    level: Optional[str] = Query(None, description="日志级别过滤"),
    step_id: Optional[int] = Query(None, description="步骤ID过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=500, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取执行日志
    
    - 支持按级别、步骤过滤
    - 支持关键词搜索
    """
    # 检查执行是否存在及权限
    result = await db.execute(
        select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )
    
    if execution.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this execution's logs"
        )
    
    # 构建查询
    query = select(ExecutionLog).where(ExecutionLog.execution_id == execution_id)
    
    if level:
        query = query.where(ExecutionLog.level == level.upper())
    
    if step_id:
        query = query.where(ExecutionLog.step_id == step_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(ExecutionLog.message.ilike(search_term))
    
    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(ExecutionLog.created_at)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [ExecutionLogResponse.model_validate(l) for l in logs]


# ============ 实时状态（WebSocket 准备） ============

@router.get(
    "/executions/{execution_id}/status",
    summary="获取执行状态（轮询）"
)
async def get_execution_status(
    execution_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取执行状态（用于轮询）
    
    返回简化的状态信息，适合前端轮询
    """
    result = await db.execute(
        select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )
    
    if execution.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this execution"
        )
    
    # 获取步骤状态摘要
    steps_result = await db.execute(
        select(
            WorkflowExecutionStep.node_id,
            WorkflowExecutionStep.status,
            WorkflowExecutionStep.started_at,
            WorkflowExecutionStep.finished_at
        ).where(WorkflowExecutionStep.execution_id == execution_id)
    )
    steps = steps_result.all()
    
    step_status = {
        "completed": 0,
        "running": 0,
        "pending": 0,
        "failed": 0
    }
    nodes_status = {}
    
    for step in steps:
        status = step.status
        if status in step_status:
            step_status[status] += 1
        nodes_status[step.node_id] = {
            "status": step.status,
            "started_at": step.started_at,
            "finished_at": step.finished_at
        }
    
    return {
        "execution_id": execution_id,
        "status": execution.status,
        "progress": {
            "total": execution.total_steps,
            "completed": execution.completed_steps,
            "failed": execution.failed_steps,
            "percentage": round(execution.completed_steps / execution.total_steps * 100, 1) if execution.total_steps > 0 else 0
        },
        "step_status": step_status,
        "nodes_status": nodes_status,
        "started_at": execution.started_at,
        "finished_at": execution.finished_at,
        "execution_time": execution.execution_time,
        "error_message": execution.error_message
    }
