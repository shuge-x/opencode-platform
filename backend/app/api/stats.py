"""
统计数据 API

提供统计数据收集和查询接口
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime, timedelta
import logging

from app.database import get_db
from app.core.security import get_current_user, get_optional_user
from app.models.user import User
from app.services.stats_service import StatsService
from app.schemas.stats import (
    OverviewStatsResponse,
    SkillStatsResponse,
    SkillTrendResponse,
    StatsExportRequest,
    StatsExportResponse,
    RecordDownloadRequest,
    RecordExecutionRequest,
    RecordViewRequest,
    RecordSearchRequest,
    PopularSkillsResponse,
    PopularSkillStats
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["Statistics"])


# ============= 总览统计 API =============

@router.get("/overview", response_model=OverviewStatsResponse)
async def get_overview_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    获取总览统计
    
    返回：
    - 总技能数
    - 总下载量
    - 总安装量
    - 平均评分
    - 今日/本周/本月统计
    """
    stats_service = StatsService(db)
    stats = await stats_service.get_overview_stats()
    
    return OverviewStatsResponse(**stats)


# ============= 技能统计 API =============

@router.get("/{skill_id}", response_model=SkillStatsResponse)
async def get_skill_stats(
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    获取技能统计
    
    返回：
    - 基本信息
    - 版本统计
    - 30天趋势
    - 评分分布
    """
    stats_service = StatsService(db)
    stats = await stats_service.get_skill_stats(skill_id)
    
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill stats not found"
        )
    
    return SkillStatsResponse(**stats)


@router.get("/{skill_id}/trend", response_model=SkillTrendResponse)
async def get_skill_trend(
    skill_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    interval: str = Query("day", description="间隔: day, week, month"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    获取技能趋势数据
    
    参数：
    - skill_id: 技能ID
    - start_date: 开始日期（默认30天前）
    - end_date: 结束日期（默认今天）
    - interval: 数据间隔（day/week/month）
    
    返回：
    - 按日期聚合的统计数据
    """
    stats_service = StatsService(db)
    trend = await stats_service.get_skill_trend(
        skill_id=skill_id,
        start_date=start_date,
        end_date=end_date,
        interval=interval
    )
    
    return SkillTrendResponse(**trend)


# ============= 数据导出 API =============

@router.post("/export", response_model=StatsExportResponse)
async def export_stats(
    request: StatsExportRequest = Body(default=StatsExportRequest()),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出统计数据
    
    需要登录。支持导出格式：
    - csv: CSV格式
    - json: JSON格式
    
    参数：
    - format: 导出格式
    - start_date: 开始日期
    - end_date: 结束日期
    - skill_ids: 指定技能ID列表
    """
    stats_service = StatsService(db)
    
    try:
        data = await stats_service.export_stats(
            format=request.format,
            start_date=request.start_date,
            end_date=request.end_date,
            skill_ids=request.skill_ids
        )
        
        # 生成文件名
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        extension = "csv" if request.format == "csv" else "json"
        filename = f"stats_export_{timestamp}.{extension}"
        
        # 计算记录数
        if request.format == "csv":
            record_count = len(data.strip().split('\n')) - 1  # 减去表头
        else:
            import json
            record_count = len(json.loads(data))
        
        return StatsExportResponse(
            format=request.format,
            data=data,
            filename=filename,
            record_count=record_count,
            generated_at=datetime.utcnow().isoformat()
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/export/download")
async def download_stats_export(
    format: str = Query("csv", description="导出格式: csv, json"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    skill_ids: Optional[str] = Query(None, description="技能ID列表，逗号分隔"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    下载统计导出文件
    
    直接返回文件内容，便于下载
    """
    stats_service = StatsService(db)
    
    # 解析技能ID列表
    ids_list = None
    if skill_ids:
        try:
            ids_list = [int(x.strip()) for x in skill_ids.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid skill_ids format"
            )
    
    try:
        data = await stats_service.export_stats(
            format=format,
            start_date=start_date,
            end_date=end_date,
            skill_ids=ids_list
        )
        
        # 生成文件名
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        extension = "csv" if format == "csv" else "json"
        filename = f"stats_export_{timestamp}.{extension}"
        
        media_type = "text/csv" if format == "csv" else "application/json"
        
        return Response(
            content=data,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============= 数据记录 API =============

@router.post("/record/download", status_code=status.HTTP_204_NO_CONTENT)
async def record_download(
    request: RecordDownloadRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    记录下载
    
    用于统计下载量。可以匿名记录。
    """
    stats_service = StatsService(db)
    user_id = current_user.id if current_user else None
    
    success = await stats_service.record_download(
        skill_id=request.skill_id,
        user_id=user_id,
        package_id=request.package_id,
        version=request.version
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record download"
        )


@router.post("/record/install", status_code=status.HTTP_204_NO_CONTENT)
async def record_install(
    skill_id: int = Body(..., embed=True),
    package_id: Optional[int] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    记录安装
    
    用于统计安装量。可以匿名记录。
    """
    stats_service = StatsService(db)
    user_id = current_user.id if current_user else None
    
    success = await stats_service.record_install(
        skill_id=skill_id,
        user_id=user_id,
        package_id=package_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record install"
        )


@router.post("/record/execution", status_code=status.HTTP_204_NO_CONTENT)
async def record_execution(
    request: RecordExecutionRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    记录执行
    
    用于统计技能使用量。记录执行类型、结果、时长等。
    """
    stats_service = StatsService(db)
    user_id = current_user.id if current_user else None
    
    success = await stats_service.record_execution(
        skill_id=request.skill_id,
        user_id=user_id,
        session_id=request.session_id,
        package_id=request.package_id,
        version=request.version,
        execution_type=request.execution_type,
        status=request.status,
        duration_ms=request.duration_ms,
        error_message=request.error_message,
        metadata=request.metadata
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record execution"
        )


@router.post("/record/view", status_code=status.HTTP_204_NO_CONTENT)
async def record_view(
    request: RecordViewRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    记录浏览
    
    用于统计技能浏览量。记录来源和referrer。
    """
    stats_service = StatsService(db)
    user_id = current_user.id if current_user else None
    
    success = await stats_service.record_view(
        skill_id=request.skill_id,
        user_id=user_id,
        source=request.source,
        referrer=request.referrer
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record view"
        )


@router.post("/record/search", status_code=status.HTTP_204_NO_CONTENT)
async def record_search(
    request: RecordSearchRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    记录搜索
    
    用于分析搜索行为。记录搜索词、筛选条件、结果数量。
    """
    stats_service = StatsService(db)
    user_id = current_user.id if current_user else None
    
    success = await stats_service.record_search(
        query=request.query,
        user_id=user_id,
        filters=request.filters,
        result_count=request.result_count,
        clicked_skill_id=request.clicked_skill_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record search"
        )


# ============= 热门统计 API =============

@router.get("/popular/overview", response_model=PopularSkillsResponse)
async def get_popular_stats(
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    period: str = Query("week", description="统计周期: day, week, month"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取热门技能统计
    
    返回各维度的热门技能：
    - 按下载量
    - 按安装量
    - 按浏览量
    - 按增长率
    """
    from sqlalchemy import select, func, desc
    from app.models.published_skill import PublishedSkill
    from app.models.skill_stats import SkillDailyStats
    
    stats_service = StatsService(db)
    
    # 计算时间范围
    today = date.today()
    if period == "day":
        start_date = today
    elif period == "week":
        start_date = today - timedelta(days=7)
    else:  # month
        start_date = today - timedelta(days=30)
    
    # 按下载量排行
    downloads_query = (
        select(
            SkillDailyStats.skill_id,
            func.sum(SkillDailyStats.download_count).label("total_downloads"),
            func.sum(SkillDailyStats.install_count).label("total_installs"),
            func.sum(SkillDailyStats.view_count).label("total_views"),
            func.sum(SkillDailyStats.execution_count).label("total_executions")
        )
        .where(SkillDailyStats.stat_date >= start_date)
        .group_by(SkillDailyStats.skill_id)
        .order_by(desc("total_downloads"))
        .limit(limit)
    )
    
    downloads_result = await db.execute(downloads_query)
    downloads_rows = downloads_result.all()
    
    # 获取技能信息并构建响应
    async def build_skill_stats(rows, value_field):
        result = []
        for row in rows:
            skill_result = await db.execute(
                select(PublishedSkill).where(PublishedSkill.id == row.skill_id)
            )
            skill = skill_result.scalar_one_or_none()
            if skill:
                result.append(PopularSkillStats(
                    skill_id=skill.id,
                    name=skill.name,
                    slug=skill.slug,
                    downloads=row.total_downloads or 0,
                    installs=row.total_installs or 0,
                    views=row.total_views or 0,
                    executions=row.total_executions or 0,
                    rating=float(skill.rating or 0),
                    growth_rate=0.0  # TODO: 计算增长率
                ))
        return result
    
    by_downloads = await build_skill_stats(downloads_rows, "total_downloads")
    
    # 按安装量排行
    installs_query = (
        select(
            SkillDailyStats.skill_id,
            func.sum(SkillDailyStats.download_count).label("total_downloads"),
            func.sum(SkillDailyStats.install_count).label("total_installs"),
            func.sum(SkillDailyStats.view_count).label("total_views"),
            func.sum(SkillDailyStats.execution_count).label("total_executions")
        )
        .where(SkillDailyStats.stat_date >= start_date)
        .group_by(SkillDailyStats.skill_id)
        .order_by(desc("total_installs"))
        .limit(limit)
    )
    
    installs_result = await db.execute(installs_query)
    installs_rows = installs_result.all()
    by_installs = await build_skill_stats(installs_rows, "total_installs")
    
    # 按浏览量排行
    views_query = (
        select(
            SkillDailyStats.skill_id,
            func.sum(SkillDailyStats.download_count).label("total_downloads"),
            func.sum(SkillDailyStats.install_count).label("total_installs"),
            func.sum(SkillDailyStats.view_count).label("total_views"),
            func.sum(SkillDailyStats.execution_count).label("total_executions")
        )
        .where(SkillDailyStats.stat_date >= start_date)
        .group_by(SkillDailyStats.skill_id)
        .order_by(desc("total_views"))
        .limit(limit)
    )
    
    views_result = await db.execute(views_query)
    views_rows = views_result.all()
    by_views = await build_skill_stats(views_rows, "total_views")
    
    return PopularSkillsResponse(
        by_downloads=by_downloads,
        by_installs=by_installs,
        by_views=by_views,
        by_growth=[],  # TODO: 实现增长率计算
        updated_at=datetime.utcnow().isoformat()
    )
