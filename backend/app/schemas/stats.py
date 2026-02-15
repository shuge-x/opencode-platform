"""
统计数据 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime


# ============= 概览统计 =============

class PeriodStats(BaseModel):
    """时段统计"""
    downloads: int = 0
    installs: int = 0


class TodayStats(BaseModel):
    """今日统计"""
    downloads: int = 0
    installs: int = 0
    views: int = 0
    executions: int = 0


class OverviewStatsResponse(BaseModel):
    """总览统计响应"""
    total_skills: int
    total_downloads: int
    total_installs: int
    avg_rating: float
    today: TodayStats
    this_week: PeriodStats
    this_month: PeriodStats
    updated_at: str


# ============= 技能统计 =============

class VersionStats(BaseModel):
    """版本统计"""
    version: str
    download_count: int = 0
    install_count: int = 0
    active_installs: int = 0


class TrendDataPoint(BaseModel):
    """趋势数据点"""
    date: str
    downloads: int = 0
    installs: int = 0
    views: int = 0
    executions: int = 0
    new_ratings: Optional[int] = 0
    new_reviews: Optional[int] = 0


class RatingDistribution(BaseModel):
    """评分分布"""
    rating_1: int = Field(default=0, alias="1")
    rating_2: int = Field(default=0, alias="2")
    rating_3: int = Field(default=0, alias="3")
    rating_4: int = Field(default=0, alias="4")
    rating_5: int = Field(default=0, alias="5")
    total: int = 0
    avg: float = 0.0

    class Config:
        populate_by_name = True


class SkillStatsResponse(BaseModel):
    """技能统计响应"""
    skill_id: int
    name: str
    slug: str
    total_downloads: int
    total_installs: int
    rating: float
    rating_count: int
    versions: List[VersionStats] = []
    trend_30d: List[TrendDataPoint] = []
    rating_distribution: Optional[Dict[str, Any]] = None
    updated_at: str


# ============= 趋势数据 =============

class TrendDataPointSimple(BaseModel):
    """简化趋势数据点"""
    date: str
    downloads: int = 0
    installs: int = 0
    views: int = 0
    executions: int = 0


class SkillTrendResponse(BaseModel):
    """技能趋势响应"""
    skill_id: int
    interval: str  # day, week, month
    start_date: str
    end_date: str
    data: List[TrendDataPointSimple]
    updated_at: str


# ============= 导出请求 =============

class StatsExportRequest(BaseModel):
    """统计导出请求"""
    format: str = Field(default="csv", description="导出格式: csv, json")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    skill_ids: Optional[List[int]] = Field(None, description="技能ID列表，为空则导出所有")


class StatsExportResponse(BaseModel):
    """统计导出响应"""
    format: str
    data: str
    filename: str
    record_count: int
    generated_at: str


# ============= 记录请求 =============

class RecordDownloadRequest(BaseModel):
    """记录下载请求"""
    skill_id: int
    package_id: Optional[int] = None
    version: Optional[str] = None


class RecordExecutionRequest(BaseModel):
    """记录执行请求"""
    skill_id: int
    session_id: Optional[int] = None
    package_id: Optional[int] = None
    version: Optional[str] = None
    execution_type: str = "invoke"
    status: str = "success"
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class RecordViewRequest(BaseModel):
    """记录浏览请求"""
    skill_id: int
    source: Optional[str] = None
    referrer: Optional[str] = None


class RecordSearchRequest(BaseModel):
    """记录搜索请求"""
    query: str
    filters: Optional[Dict[str, Any]] = None
    result_count: int = 0
    clicked_skill_id: Optional[int] = None


# ============= 热门统计 =============

class PopularSkillStats(BaseModel):
    """热门技能统计"""
    skill_id: int
    name: str
    slug: str
    downloads: int
    installs: int
    views: int
    executions: int
    rating: float
    growth_rate: float = 0.0  # 增长率


class PopularSkillsResponse(BaseModel):
    """热门技能响应"""
    by_downloads: List[PopularSkillStats] = []
    by_installs: List[PopularSkillStats] = []
    by_views: List[PopularSkillStats] = []
    by_growth: List[PopularSkillStats] = []
    updated_at: str
