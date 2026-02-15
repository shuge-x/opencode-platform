"""
统计数据收集服务

实现统计数据收集、聚合和查询功能
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, and_, or_, case
from sqlalchemy.sql import text
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
import csv
import io

from app.models.published_skill import PublishedSkill, SkillPackage
from app.models.skill_stats import (
    SkillDailyStats,
    SkillVersionStats,
    SkillRatingDistribution,
    SkillExecutionLog,
    SkillViewLog,
    SkillSearchLog
)
from app.core.cache import cache, CacheKeys, CacheExpire

logger = logging.getLogger(__name__)


class StatsService:
    """统计数据服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============= 数据收集方法 =============

    async def record_download(
        self,
        skill_id: int,
        user_id: Optional[int] = None,
        package_id: Optional[int] = None,
        version: Optional[str] = None
    ) -> bool:
        """记录下载"""
        try:
            today = date.today()
            
            # 更新每日统计
            await self._upsert_daily_stat(
                skill_id=skill_id,
                stat_date=today,
                increment={"download_count": 1},
                unique_user=user_id
            )

            # 更新版本统计
            if package_id:
                await self._upsert_version_stat(package_id)

            # 更新技能总下载量
            await self.db.execute(
                update(PublishedSkill)
                .where(PublishedSkill.id == skill_id)
                .values(download_count=PublishedSkill.download_count + 1)
            )

            await self.db.commit()

            # 清除缓存
            await self._invalidate_skill_cache(skill_id)

            return True
        except Exception as e:
            logger.error(f"Failed to record download: {e}")
            await self.db.rollback()
            return False

    async def record_install(
        self,
        skill_id: int,
        user_id: Optional[int] = None,
        package_id: Optional[int] = None
    ) -> bool:
        """记录安装"""
        try:
            today = date.today()

            # 更新每日统计
            await self._upsert_daily_stat(
                skill_id=skill_id,
                stat_date=today,
                increment={"install_count": 1},
                unique_user=user_id
            )

            # 更新技能总安装量
            await self.db.execute(
                update(PublishedSkill)
                .where(PublishedSkill.id == skill_id)
                .values(install_count=PublishedSkill.install_count + 1)
            )

            await self.db.commit()

            await self._invalidate_skill_cache(skill_id)

            return True
        except Exception as e:
            logger.error(f"Failed to record install: {e}")
            await self.db.rollback()
            return False

    async def record_execution(
        self,
        skill_id: int,
        user_id: Optional[int] = None,
        session_id: Optional[int] = None,
        package_id: Optional[int] = None,
        version: Optional[str] = None,
        execution_type: str = "invoke",
        status: str = "success",
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """记录执行"""
        try:
            today = date.today()

            # 创建执行日志
            log = SkillExecutionLog(
                skill_id=skill_id,
                user_id=user_id,
                session_id=session_id,
                package_id=package_id,
                execution_type=execution_type,
                version=version,
                status=status,
                duration_ms=duration_ms,
                error_message=error_message,
                metadata=metadata
            )
            self.db.add(log)

            # 更新每日统计
            await self._upsert_daily_stat(
                skill_id=skill_id,
                stat_date=today,
                increment={"execution_count": 1},
                unique_user=user_id,
                unique_field="unique_executions"
            )

            await self.db.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to record execution: {e}")
            await self.db.rollback()
            return False

    async def record_view(
        self,
        skill_id: int,
        user_id: Optional[int] = None,
        source: Optional[str] = None,
        referrer: Optional[str] = None
    ) -> bool:
        """记录浏览"""
        try:
            today = date.today()

            # 创建浏览日志
            log = SkillViewLog(
                skill_id=skill_id,
                user_id=user_id,
                source=source,
                referrer=referrer
            )
            self.db.add(log)

            # 更新每日统计
            await self._upsert_daily_stat(
                skill_id=skill_id,
                stat_date=today,
                increment={"view_count": 1},
                unique_user=user_id,
                unique_field="unique_views"
            )

            await self.db.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to record view: {e}")
            await self.db.rollback()
            return False

    async def record_search(
        self,
        query: str,
        user_id: Optional[int] = None,
        filters: Optional[Dict] = None,
        result_count: int = 0,
        clicked_skill_id: Optional[int] = None
    ) -> bool:
        """记录搜索"""
        try:
            log = SkillSearchLog(
                user_id=user_id,
                query=query,
                filters=filters,
                result_count=result_count,
                clicked_skill_id=clicked_skill_id
            )
            self.db.add(log)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to record search: {e}")
            await self.db.rollback()
            return False

    async def update_rating_distribution(
        self,
        skill_id: int
    ) -> bool:
        """更新评分分布"""
        try:
            today = date.today()

            # 查询评分分布
            from app.models.published_skill import SkillRating
            result = await self.db.execute(
                select(
                    SkillRating.rating,
                    func.count(SkillRating.id).label("count")
                )
                .where(SkillRating.published_skill_id == skill_id)
                .group_by(SkillRating.rating)
            )
            rows = result.all()

            # 构建分布
            distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            total = 0
            weighted_sum = 0

            for row in rows:
                rating = row.rating
                count = row.count
                if rating in distribution:
                    distribution[rating] = count
                    total += count
                    weighted_sum += rating * count

            avg_rating = weighted_sum / total if total > 0 else 0

            # 检查是否已有记录
            existing = await self.db.execute(
                select(SkillRatingDistribution).where(
                    and_(
                        SkillRatingDistribution.skill_id == skill_id,
                        SkillRatingDistribution.stat_date == today
                    )
                )
            )
            existing_record = existing.scalar_one_or_none()

            if existing_record:
                existing_record.rating_1_count = distribution[1]
                existing_record.rating_2_count = distribution[2]
                existing_record.rating_3_count = distribution[3]
                existing_record.rating_4_count = distribution[4]
                existing_record.rating_5_count = distribution[5]
                existing_record.total_ratings = total
                existing_record.avg_rating = avg_rating
            else:
                record = SkillRatingDistribution(
                    skill_id=skill_id,
                    stat_date=today,
                    rating_1_count=distribution[1],
                    rating_2_count=distribution[2],
                    rating_3_count=distribution[3],
                    rating_4_count=distribution[4],
                    rating_5_count=distribution[5],
                    total_ratings=total,
                    avg_rating=avg_rating
                )
                self.db.add(record)

            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update rating distribution: {e}")
            await self.db.rollback()
            return False

    # ============= 统计查询方法 =============

    async def get_overview_stats(self) -> Dict[str, Any]:
        """获取总览统计"""
        cache_key = "stats:overview"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        # 总技能数
        total_skills_result = await self.db.execute(
            select(func.count()).select_from(PublishedSkill).where(
                PublishedSkill.status == "published"
            )
        )
        total_skills = total_skills_result.scalar()

        # 总下载量
        downloads_result = await self.db.execute(
            select(func.sum(PublishedSkill.download_count)).where(
                PublishedSkill.status == "published"
            )
        )
        total_downloads = downloads_result.scalar() or 0

        # 总安装量
        installs_result = await self.db.execute(
            select(func.sum(PublishedSkill.install_count)).where(
                PublishedSkill.status == "published"
            )
        )
        total_installs = installs_result.scalar() or 0

        # 平均评分
        rating_result = await self.db.execute(
            select(func.avg(PublishedSkill.rating)).where(
                and_(
                    PublishedSkill.status == "published",
                    PublishedSkill.rating_count > 0
                )
            )
        )
        avg_rating = float(rating_result.scalar() or 0)

        # 今日统计
        today = date.today()
        today_stats = await self.db.execute(
            select(
                func.sum(SkillDailyStats.download_count).label("downloads"),
                func.sum(SkillDailyStats.install_count).label("installs"),
                func.sum(SkillDailyStats.view_count).label("views"),
                func.sum(SkillDailyStats.execution_count).label("executions")
            ).where(SkillDailyStats.stat_date == today)
        )
        today_row = today_stats.first()

        # 本周统计
        week_start = today - timedelta(days=today.weekday())
        week_stats = await self.db.execute(
            select(
                func.sum(SkillDailyStats.download_count).label("downloads"),
                func.sum(SkillDailyStats.install_count).label("installs")
            ).where(SkillDailyStats.stat_date >= week_start)
        )
        week_row = week_stats.first()

        # 本月统计
        month_start = today.replace(day=1)
        month_stats = await self.db.execute(
            select(
                func.sum(SkillDailyStats.download_count).label("downloads"),
                func.sum(SkillDailyStats.install_count).label("installs")
            ).where(SkillDailyStats.stat_date >= month_start)
        )
        month_row = month_stats.first()

        stats = {
            "total_skills": total_skills,
            "total_downloads": total_downloads,
            "total_installs": total_installs,
            "avg_rating": round(avg_rating, 2),
            "today": {
                "downloads": today_row.downloads or 0,
                "installs": today_row.installs or 0,
                "views": today_row.views or 0,
                "executions": today_row.executions or 0
            },
            "this_week": {
                "downloads": week_row.downloads or 0,
                "installs": week_row.installs or 0
            },
            "this_month": {
                "downloads": month_row.downloads or 0,
                "installs": month_row.installs or 0
            },
            "updated_at": datetime.utcnow().isoformat()
        }

        # 缓存5分钟
        await cache.set(cache_key, stats, expire=300)

        return stats

    async def get_skill_stats(self, skill_id: int) -> Dict[str, Any]:
        """获取技能统计"""
        cache_key = f"stats:skill:{skill_id}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        # 获取技能基本信息
        skill_result = await self.db.execute(
            select(PublishedSkill).where(PublishedSkill.id == skill_id)
        )
        skill = skill_result.scalar_one_or_none()
        if not skill:
            return {}

        # 获取各版本下载量
        version_stats = await self.db.execute(
            select(
                SkillPackage.version,
                SkillPackage.download_count,
                SkillVersionStats.install_count,
                SkillVersionStats.active_installs
            )
            .outerjoin(SkillVersionStats, SkillPackage.id == SkillVersionStats.package_id)
            .where(SkillPackage.published_skill_id == skill_id)
            .order_by(SkillPackage.version_code.desc())
        )
        versions = []
        for row in version_stats.all():
            versions.append({
                "version": row.version,
                "download_count": row.download_count,
                "install_count": row.install_count or 0,
                "active_installs": row.active_installs or 0
            })

        # 最近30天趋势
        trend_start = date.today() - timedelta(days=30)
        daily_stats = await self.db.execute(
            select(SkillDailyStats)
            .where(
                and_(
                    SkillDailyStats.skill_id == skill_id,
                    SkillDailyStats.stat_date >= trend_start
                )
            )
            .order_by(SkillDailyStats.stat_date.asc())
        )
        trend = []
        for stat in daily_stats.scalars().all():
            trend.append({
                "date": stat.stat_date.isoformat(),
                "downloads": stat.download_count,
                "installs": stat.install_count,
                "views": stat.view_count,
                "executions": stat.execution_count
            })

        # 评分分布
        rating_dist = await self.db.execute(
            select(SkillRatingDistribution)
            .where(SkillRatingDistribution.skill_id == skill_id)
            .order_by(SkillRatingDistribution.stat_date.desc())
            .limit(1)
        )
        rating_row = rating_dist.scalar_one_or_none()

        rating_distribution = None
        if rating_row:
            rating_distribution = {
                "1": rating_row.rating_1_count,
                "2": rating_row.rating_2_count,
                "3": rating_row.rating_3_count,
                "4": rating_row.rating_4_count,
                "5": rating_row.rating_5_count,
                "total": rating_row.total_ratings,
                "avg": float(rating_row.avg_rating)
            }

        stats = {
            "skill_id": skill_id,
            "name": skill.name,
            "slug": skill.slug,
            "total_downloads": skill.download_count,
            "total_installs": skill.install_count,
            "rating": float(skill.rating),
            "rating_count": skill.rating_count,
            "versions": versions,
            "trend_30d": trend,
            "rating_distribution": rating_distribution,
            "updated_at": datetime.utcnow().isoformat()
        }

        # 缓存5分钟
        await cache.set(cache_key, stats, expire=300)

        return stats

    async def get_skill_trend(
        self,
        skill_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        interval: str = "day"  # day, week, month
    ) -> Dict[str, Any]:
        """获取技能趋势数据"""
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        cache_key = f"stats:trend:{skill_id}:{start_date}:{end_date}:{interval}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        # 查询趋势数据
        if interval == "day":
            query = select(SkillDailyStats).where(
                and_(
                    SkillDailyStats.skill_id == skill_id,
                    SkillDailyStats.stat_date >= start_date,
                    SkillDailyStats.stat_date <= end_date
                )
            ).order_by(SkillDailyStats.stat_date.asc())

            result = await self.db.execute(query)
            stats = result.scalars().all()

            trend_data = []
            for stat in stats:
                trend_data.append({
                    "date": stat.stat_date.isoformat(),
                    "downloads": stat.download_count,
                    "installs": stat.install_count,
                    "views": stat.view_count,
                    "executions": stat.execution_count,
                    "new_ratings": stat.new_ratings,
                    "new_reviews": stat.new_reviews
                })

        elif interval == "week":
            # 按周聚合
            query = text("""
                SELECT 
                    DATE_TRUNC('week', stat_date) as week_start,
                    SUM(download_count) as downloads,
                    SUM(install_count) as installs,
                    SUM(view_count) as views,
                    SUM(execution_count) as executions
                FROM skill_daily_stats
                WHERE skill_id = :skill_id
                AND stat_date >= :start_date
                AND stat_date <= :end_date
                GROUP BY DATE_TRUNC('week', stat_date)
                ORDER BY week_start
            """)
            result = await self.db.execute(
                query,
                {"skill_id": skill_id, "start_date": start_date, "end_date": end_date}
            )
            rows = result.all()

            trend_data = []
            for row in rows:
                trend_data.append({
                    "date": row.week_start.isoformat(),
                    "downloads": row.downloads,
                    "installs": row.installs,
                    "views": row.views,
                    "executions": row.executions
                })

        elif interval == "month":
            # 按月聚合
            query = text("""
                SELECT 
                    DATE_TRUNC('month', stat_date) as month_start,
                    SUM(download_count) as downloads,
                    SUM(install_count) as installs,
                    SUM(view_count) as views,
                    SUM(execution_count) as executions
                FROM skill_daily_stats
                WHERE skill_id = :skill_id
                AND stat_date >= :start_date
                AND stat_date <= :end_date
                GROUP BY DATE_TRUNC('month', stat_date)
                ORDER BY month_start
            """)
            result = await self.db.execute(
                query,
                {"skill_id": skill_id, "start_date": start_date, "end_date": end_date}
            )
            rows = result.all()

            trend_data = []
            for row in rows:
                trend_data.append({
                    "date": row.month_start.isoformat(),
                    "downloads": row.downloads,
                    "installs": row.installs,
                    "views": row.views,
                    "executions": row.executions
                })
        else:
            trend_data = []

        result_data = {
            "skill_id": skill_id,
            "interval": interval,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "data": trend_data,
            "updated_at": datetime.utcnow().isoformat()
        }

        # 缓存10分钟
        await cache.set(cache_key, result_data, expire=600)

        return result_data

    async def export_stats(
        self,
        format: str = "csv",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skill_ids: Optional[List[int]] = None
    ) -> str:
        """导出统计数据"""
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        # 查询数据
        query = select(SkillDailyStats).where(
            and_(
                SkillDailyStats.stat_date >= start_date,
                SkillDailyStats.stat_date <= end_date
            )
        )

        if skill_ids:
            query = query.where(SkillDailyStats.skill_id.in_(skill_ids))

        query = query.order_by(SkillDailyStats.stat_date.desc())

        result = await self.db.execute(query)
        stats = result.scalars().all()

        if format == "csv":
            return self._export_csv(stats)
        elif format == "json":
            return self._export_json(stats)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_csv(self, stats: List[SkillDailyStats]) -> str:
        """导出为CSV"""
        output = io.StringIO()
        writer = csv.writer(output)

        # 表头
        writer.writerow([
            "skill_id", "stat_date", "download_count", "unique_downloads",
            "install_count", "unique_installs", "execution_count", "unique_executions",
            "view_count", "unique_views", "new_ratings", "new_reviews"
        ])

        # 数据
        for stat in stats:
            writer.writerow([
                stat.skill_id,
                stat.stat_date.isoformat(),
                stat.download_count,
                stat.unique_downloads,
                stat.install_count,
                stat.unique_installs,
                stat.execution_count,
                stat.unique_executions,
                stat.view_count,
                stat.unique_views,
                stat.new_ratings,
                stat.new_reviews
            ])

        return output.getvalue()

    def _export_json(self, stats: List[SkillDailyStats]) -> str:
        """导出为JSON"""
        import json
        data = []
        for stat in stats:
            data.append({
                "skill_id": stat.skill_id,
                "stat_date": stat.stat_date.isoformat(),
                "download_count": stat.download_count,
                "unique_downloads": stat.unique_downloads,
                "install_count": stat.install_count,
                "unique_installs": stat.unique_installs,
                "execution_count": stat.execution_count,
                "unique_executions": stat.unique_executions,
                "view_count": stat.view_count,
                "unique_views": stat.unique_views,
                "new_ratings": stat.new_ratings,
                "new_reviews": stat.new_reviews
            })
        return json.dumps(data, indent=2)

    # ============= 私有辅助方法 =============

    async def _upsert_daily_stat(
        self,
        skill_id: int,
        stat_date: date,
        increment: Dict[str, int],
        unique_user: Optional[int] = None,
        unique_field: Optional[str] = "unique_downloads"
    ) -> None:
        """更新或插入每日统计"""
        # 查找现有记录
        result = await self.db.execute(
            select(SkillDailyStats).where(
                and_(
                    SkillDailyStats.skill_id == skill_id,
                    SkillDailyStats.stat_date == stat_date
                )
            )
        )
        stat = result.scalar_one_or_none()

        if stat:
            # 更新现有记录
            for field, value in increment.items():
                current = getattr(stat, field, 0)
                setattr(stat, field, current + value)

            # 如果有唯一用户，记录到唯一字段
            if unique_user and unique_field:
                # 这里简化处理，实际应该用Redis bitmap或类似技术
                pass
        else:
            # 创建新记录
            stat = SkillDailyStats(
                skill_id=skill_id,
                stat_date=stat_date,
                **increment
            )
            self.db.add(stat)

    async def _upsert_version_stat(self, package_id: int) -> None:
        """更新或插入版本统计"""
        result = await self.db.execute(
            select(SkillVersionStats).where(SkillVersionStats.package_id == package_id)
        )
        stat = result.scalar_one_or_none()

        if stat:
            stat.download_count += 1
        else:
            stat = SkillVersionStats(
                package_id=package_id,
                download_count=1
            )
            self.db.add(stat)

    async def _invalidate_skill_cache(self, skill_id: int) -> None:
        """清除技能相关缓存"""
        await cache.delete_pattern(f"stats:skill:{skill_id}*")
        await cache.delete_pattern(f"stats:trend:{skill_id}*")
        await cache.delete_pattern("stats:overview*")
        await cache.delete_pattern(f"skill:detail:{skill_id}*")
