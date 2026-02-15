"""
技能监控 API

提供监控数据查询接口
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

from app.database import get_db
from app.core.security import get_current_user, get_optional_user
from app.models.user import User
from app.services.skill_monitoring_service import SkillMonitoringService
from app.core.skill_metrics import SKILL_INVOCATION_DURATION

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["Skill Monitoring"])


# ============= 请求/响应模型 =============

class InvocationLogResponse(BaseModel):
    """调用日志响应"""
    id: int
    skill_id: int
    skill_name: str
    skill_version: Optional[str] = None
    execution_type: str
    status: str
    user_id: Optional[int] = None
    session_id: Optional[int] = None
    request_id: Optional[str] = None
    input_params: Optional[dict] = None
    output_data: Optional[str] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    duration_ms: Optional[int] = None
    memory_bytes: Optional[int] = None
    cpu_percent: Optional[float] = None
    started_at: str
    completed_at: Optional[str] = None

    class Config:
        from_attributes = True


class PerformanceStatsResponse(BaseModel):
    """性能统计响应"""
    period: dict
    invocations: dict
    duration: dict
    throughput: dict


class SkillRankingItem(BaseModel):
    """技能排行项"""
    skill_id: int
    skill_name: str
    total_invocations: int
    avg_duration_ms: Optional[float] = None
    success_count: int
    error_count: int
    error_rate: float


class ErrorLogResponse(BaseModel):
    """错误日志响应"""
    id: int
    skill_id: int
    skill_name: str
    error_type: str
    error_message: Optional[str] = None
    occurrence_count: int
    last_occurred_at: str
    first_occurred_at: str

    class Config:
        from_attributes = True


class ErrorSummaryResponse(BaseModel):
    """错误摘要响应"""
    period: dict
    by_type: List[dict]
    by_skill: List[dict]


class RealtimeStatsResponse(BaseModel):
    """实时统计响应"""
    skill_id: int
    date: str
    invocations: int
    success_count: int
    error_count: int
    avg_duration_ms: Optional[float] = None


# ============= Prometheus 指标端点 =============

@router.get("/metrics", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """
    Prometheus 指标端点
    
    返回 Prometheus 格式的监控指标
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    metrics = generate_latest()
    return PlainTextResponse(
        content=metrics.decode('utf-8'),
        media_type=CONTENT_TYPE_LATEST
    )


# ============= 调用日志 API =============

@router.get("/invocations", response_model=List[InvocationLogResponse])
async def list_invocation_logs(
    skill_id: Optional[int] = Query(None, description="技能ID"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    status: Optional[str] = Query(None, description="执行状态: success, error, timeout"),
    execution_type: Optional[str] = Query(None, description="执行类型: api, websocket, scheduled"),
    error_type: Optional[str] = Query(None, description="错误类型"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询调用日志
    
    需要登录。支持按技能、用户、状态等条件过滤。
    """
    monitoring_service = SkillMonitoringService(db)
    logs = await monitoring_service.query_invocation_logs(
        skill_id=skill_id,
        user_id=user_id,
        status=status,
        execution_type=execution_type,
        error_type=error_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset
    )
    
    return [InvocationLogResponse(**log.to_dict()) for log in logs]


@router.get("/invocations/{log_id}", response_model=InvocationLogResponse)
async def get_invocation_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单条调用日志详情
    
    需要登录。
    """
    monitoring_service = SkillMonitoringService(db)
    log = await monitoring_service.get_invocation_log(log_id)
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invocation log not found"
        )
    
    return InvocationLogResponse(**log.to_dict())


# ============= 性能统计 API =============

@router.get("/stats/performance", response_model=PerformanceStatsResponse)
async def get_performance_stats(
    skill_id: Optional[int] = Query(None, description="技能ID（可选，不指定则统计所有）"),
    hours: int = Query(24, ge=1, le=720, description="统计时长（小时）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取性能统计
    
    需要登录。返回响应时间、吞吐量、错误率等统计。
    
    查询参数：
    - skill_id: 技能ID（可选）
    - hours: 统计时长（默认24小时）
    """
    monitoring_service = SkillMonitoringService(db)
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    end_time = datetime.utcnow()
    
    stats = await monitoring_service.get_performance_stats(
        skill_id=skill_id,
        start_time=start_time,
        end_time=end_time
    )
    
    return PerformanceStatsResponse(**stats)


@router.get("/stats/rankings", response_model=List[SkillRankingItem])
async def get_skill_rankings(
    metric: str = Query("invocations", description="排序指标: invocations, errors, avg_duration"),
    hours: int = Query(24, ge=1, le=720, description="统计时长（小时）"),
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取技能排行榜
    
    需要登录。按指定指标排序返回技能列表。
    
    查询参数：
    - metric: 排序指标（invocations/errors/avg_duration）
    - hours: 统计时长（默认24小时）
    - limit: 返回数量
    """
    monitoring_service = SkillMonitoringService(db)
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    end_time = datetime.utcnow()
    
    rankings = await monitoring_service.get_skill_rankings(
        metric=metric,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    return [SkillRankingItem(**item) for item in rankings]


@router.get("/stats/realtime/{skill_id}", response_model=RealtimeStatsResponse)
async def get_realtime_stats(
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取技能实时统计
    
    需要登录。从 Redis 获取今日实时统计数据。
    """
    monitoring_service = SkillMonitoringService(db)
    stats = await monitoring_service.get_realtime_stats(skill_id)
    
    if "error" in stats:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=stats["error"]
        )
    
    return RealtimeStatsResponse(**stats)


# ============= 错误追踪 API =============

@router.get("/errors", response_model=List[ErrorLogResponse])
async def list_error_logs(
    skill_id: Optional[int] = Query(None, description="技能ID"),
    error_type: Optional[str] = Query(None, description="错误类型"),
    hours: int = Query(24, ge=1, le=720, description="统计时长（小时）"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询错误日志
    
    需要登录。返回聚合后的错误列表。
    """
    monitoring_service = SkillMonitoringService(db)
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    end_time = datetime.utcnow()
    
    errors = await monitoring_service.get_error_logs(
        skill_id=skill_id,
        error_type=error_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    return [ErrorLogResponse(**error.to_dict()) for error in errors]


@router.get("/errors/summary", response_model=ErrorSummaryResponse)
async def get_error_summary(
    hours: int = Query(24, ge=1, le=720, description="统计时长（小时）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取错误摘要
    
    需要登录。返回按错误类型和技能分组的错误统计。
    """
    monitoring_service = SkillMonitoringService(db)
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    end_time = datetime.utcnow()
    
    summary = await monitoring_service.get_error_summary(
        start_time=start_time,
        end_time=end_time
    )
    
    return ErrorSummaryResponse(**summary)


# ============= 仪表板数据 API =============

@router.get("/dashboard")
async def get_dashboard_data(
    hours: int = Query(24, ge=1, le=168, description="统计时长（小时）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取仪表板数据
    
    需要登录。返回仪表板所需的所有监控数据。
    """
    monitoring_service = SkillMonitoringService(db)
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    end_time = datetime.utcnow()
    
    # 获取总体性能统计
    overall_stats = await monitoring_service.get_performance_stats(
        start_time=start_time,
        end_time=end_time
    )
    
    # 获取排行榜
    top_by_invocations = await monitoring_service.get_skill_rankings(
        metric="invocations",
        start_time=start_time,
        end_time=end_time,
        limit=10
    )
    
    top_by_errors = await monitoring_service.get_skill_rankings(
        metric="errors",
        start_time=start_time,
        end_time=end_time,
        limit=10
    )
    
    # 获取错误摘要
    error_summary = await monitoring_service.get_error_summary(
        start_time=start_time,
        end_time=end_time
    )
    
    # 获取最近的错误
    recent_errors = await monitoring_service.get_error_logs(
        start_time=start_time,
        end_time=end_time,
        limit=10
    )
    
    return {
        "period": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "hours": hours
        },
        "overall_stats": overall_stats,
        "rankings": {
            "by_invocations": top_by_invocations,
            "by_errors": top_by_errors
        },
        "errors": {
            "summary": error_summary,
            "recent": [error.to_dict() for error in recent_errors]
        }
    }
