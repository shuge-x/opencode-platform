"""
技能执行 API - Sprint 7
"""
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.skill import Skill, SkillExecution, SkillExecutionLog
from app.schemas.skill import SkillExecutionCreate, SkillExecutionResponse
from app.core.skill_executor import skill_sandbox
from datetime import datetime

router = APIRouter()


@router.post("/execute", response_model=SkillExecutionResponse, status_code=status.HTTP_201_CREATED)
async def execute_skill(
    execution: SkillExecutionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    执行技能

    - 创建执行记录
    - 在 Docker 沙箱中执行
    - 返回执行结果
    """
    # 查询技能
    result = await db.execute(
        select(Skill).where(
            Skill.id == execution.skill_id,
            Skill.user_id == current_user.id
        )
    )
    skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )

    # 创建执行记录
    db_execution = SkillExecution(
        skill_id=skill.id,
        user_id=current_user.id,
        status="pending",
        input_params=execution.input_params
    )

    db.add(db_execution)
    await db.commit()
    await db.refresh(db_execution)

    # 异步执行技能
    background_tasks.add_task(
        execute_skill_background,
        db_execution.id,
        skill,
        execution.input_params,
        current_user.id
    )

    return db_execution


async def execute_skill_background(
    execution_id: int,
    skill: Skill,
    params: dict,
    user_id: int
):
    """
    后台执行技能

    Args:
        execution_id: 执行记录ID
        skill: 技能对象
        params: 输入参数
        user_id: 用户ID
    """
    from app.database import async_session_maker

    async with async_session_maker() as db:
        try:
            # 更新状态为运行中
            result = await db.execute(
                select(SkillExecution).where(SkillExecution.id == execution_id)
            )
            db_execution = result.scalar_one()

            db_execution.status = "running"
            db_execution.started_at = datetime.utcnow()
            await db.commit()

            # 准备文件内容
            files = {}
            for file in skill.files:
                files[file.filename] = file.content or ""

            # 执行技能
            execution_result = await skill_sandbox.execute_skill(
                skill_id=skill.id,
                files=files,
                main_file="main.py",
                params=params,
                user_id=user_id
            )

            # 更新执行结果
            db_execution.completed_at = datetime.utcnow()
            db_execution.execution_time = execution_result.get("execution_time", 0)
            db_execution.container_id = execution_result.get("container_id")

            if execution_result["success"]:
                db_execution.status = "success"
                db_execution.output_result = execution_result["output"]

                # 添加日志
                log = SkillExecutionLog(
                    execution_id=execution_id,
                    log_level="INFO",
                    message="技能执行成功"
                )
                db.add(log)
            else:
                db_execution.status = "failed"
                db_execution.error_message = execution_result.get("error", "Unknown error")

                # 添加错误日志
                log = SkillExecutionLog(
                    execution_id=execution_id,
                    log_level="ERROR",
                    message=execution_result.get("error", "Unknown error")
                )
                db.add(log)

            # 更新技能统计
            skill.execution_count += 1
            if db_execution.status == "success":
                skill.success_count += 1
            else:
                skill.failure_count += 1

            await db.commit()

        except Exception as e:
            logger.error(f"Background execution error: {e}", exc_info=True)

            # 更新状态为失败
            result = await db.execute(
                select(SkillExecution).where(SkillExecution.id == execution_id)
            )
            db_execution = result.scalar_one()

            db_execution.status = "failed"
            db_execution.error_message = str(e)
            db_execution.completed_at = datetime.utcnow()

            await db.commit()


@router.get("/executions/{execution_id}", response_model=SkillExecutionResponse)
async def get_execution(
    execution_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取执行结果
    """
    result = await db.execute(
        select(SkillExecution).where(
            SkillExecution.id == execution_id,
            SkillExecution.user_id == current_user.id
        )
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )

    return execution


@router.get("/executions/{execution_id}/logs")
async def get_execution_logs(
    execution_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取执行日志
    """
    result = await db.execute(
        select(SkillExecution).where(
            SkillExecution.id == execution_id,
            SkillExecution.user_id == current_user.id
        )
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )

    return execution.logs
