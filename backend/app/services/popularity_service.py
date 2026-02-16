"""
热度计算服务

计算技能热度分数，基于：
- 下载量统计
- 使用量统计
- 评分权重
- 时间衰减
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, and_, case
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import math

from app.models.published_skill import PublishedSkill, SkillPackage, SkillReview
from app.models.category import SkillCategory
from app.core.cache import cache, CacheKeys, CacheExpire

logger = logging.getLogger(__name__)


class PopularityService:
    """热度计算服务"""

    # 权重配置
    WEIGHT_DOWNLOAD = 0.35  # 下载量权重
    WEIGHT_INSTALL = 0.25   # 使用量权重
    WEIGHT_RATING = 0.25    # 评分权重
    WEIGHT_RECENCY = 0.15   # 时间新鲜度权重

    # 时间衰减配置
    DECAY_HALF_LIFE_DAYS = 30  # 半衰期30天

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_popularity_score(
        self,
        skill_id: int,
        download_count: Optional[int] = None,
        install_count: Optional[int] = None,
        rating: Optional[Decimal] = None,
        rating_count: Optional[int] = None,
        published_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ) -> float:
        """
        计算单个技能的热度分数

        Args:
            skill_id: 技能ID
            download_count: 下载量
            install_count: 使用量
            rating: 平均评分
            rating_count: 评价数量
            published_at: 发布时间
            updated_at: 更新时间

        Returns:
            float: 热度分数 (0-1000+)
        """
        # 获取技能数据（如果未提供）
        if download_count is None:
            result = await self.db.execute(
                select(PublishedSkill).where(PublishedSkill.id == skill_id)
            )
            skill = result.scalar_one_or_none()
            if not skill:
                return 0.0

            download_count = skill.download_count
            install_count = skill.install_count
            rating = skill.rating
            rating_count = skill.rating_count
            published_at = skill.published_at
            updated_at = skill.updated_at

        # 计算各维度分数

        # 1. 下载量分数 (归一化到 0-100)
        download_score = self._normalize_count(download_count or 0, max_val=10000) * 100

        # 2. 使用量分数 (归一化到 0-100)
        install_score = self._normalize_count(install_count or 0, max_val=5000) * 100

        # 3. 评分分数 (考虑评分和评价数量)
        rating_score = await self._calculate_rating_score(
            float(rating or 0), rating_count or 0
        )

        # 4. 时间新鲜度分数
        recency_score = self._calculate_recency_score(
            updated_at or published_at or datetime.utcnow()
        )

        # 加权计算总分
        total_score = (
            download_score * self.WEIGHT_DOWNLOAD +
            install_score * self.WEIGHT_INSTALL +
            rating_score * self.WEIGHT_RATING +
            recency_score * self.WEIGHT_RECENCY
        )

        return round(total_score, 2)

    def _normalize_count(self, count: int, max_val: int = 10000) -> float:
        """
        归一化计数（使用对数缩放）

        使用 log(count + 1) / log(max_val + 1) 将任意计数归一化到 0-1
        """
        if count <= 0:
            return 0.0
        if count >= max_val:
            return 1.0
        return math.log(count + 1) / math.log(max_val + 1)

    async def _calculate_rating_score(self, rating: float, rating_count: int) -> float:
        """
        计算评分分数

        结合评分和评价数量，使用贝叶斯平均避免少量评价的偏差
        """
        if rating_count == 0:
            return 50.0  # 无评价的默认分数

        # 贝叶斯平均参数
        # 假设全局平均评分为 3.5，最少评价数为 5
        global_avg = 3.5
        min_ratings = 5

        # 贝叶斯平均
        bayesian_avg = (
            (min_ratings * global_avg + rating_count * rating) /
            (min_ratings + rating_count)
        )

        # 转换为 0-100 分数
        score = (bayesian_avg / 5.0) * 100

        return round(score, 2)

    def _calculate_recency_score(self, timestamp: datetime) -> float:
        """
        计算时间新鲜度分数

        使用指数衰减，新鲜的内容得分更高
        """
        now = datetime.utcnow()
        delta = now - timestamp
        days_old = delta.total_seconds() / 86400  # 转换为天数

        # 指数衰减
        # score = 100 * 2^(-days / half_life)
        decay_factor = math.pow(2, -days_old / self.DECAY_HALF_LIFE_DAYS)
        score = 100 * decay_factor

        return round(max(0, score), 2)

    async def batch_update_popularity_scores(
        self,
        skill_ids: Optional[List[int]] = None,
        batch_size: int = 100
    ) -> int:
        """
        批量更新热度分数

        Args:
            skill_ids: 指定技能ID列表，如果为None则更新所有
            batch_size: 批处理大小

        Returns:
            int: 更新的技能数量
        """
        query = select(PublishedSkill).where(
            PublishedSkill.status == "published"
        )

        if skill_ids:
            query = query.where(PublishedSkill.id.in_(skill_ids))

        result = await self.db.execute(query)
        skills = result.scalars().all()

        updated_count = 0

        for skill in skills:
            score = await self.calculate_popularity_score(
                skill_id=skill.id,
                download_count=skill.download_count,
                install_count=skill.install_count,
                rating=skill.rating,
                rating_count=skill.rating_count,
                published_at=skill.published_at,
                updated_at=skill.updated_at
            )

            # 更新分数（存储在 JSON 字段或新字段中）
            # 由于 PublishedSkill 没有 popularity_score 字段，我们使用元数据存储
            # 或者实时计算。这里我们可以添加一个新字段或使用缓存

            # 暂存到 Redis 有序集合
            if cache._connected and cache.client:
                await cache.client.zadd(
                    "skills:popularity",
                    {str(skill.id): score}
                )

            updated_count += 1

            # 批量提交
            if updated_count % batch_size == 0:
                await self.db.commit()

        if updated_count % batch_size != 0:
            await self.db.commit()

        logger.info(f"Updated popularity scores for {updated_count} skills")
        return updated_count

    async def get_top_skills_by_popularity(
        self,
        limit: int = 100,
        category_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取热门技能排行

        Args:
            limit: 返回数量
            category_id: 分类ID过滤

        Returns:
            List[Dict]: 热门技能列表
        """
        cache_key = f"skills:top:popular:{category_id or 'all'}:{limit}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        # 实时计算热门排行
        query = select(PublishedSkill).where(
            and_(
                PublishedSkill.is_public == True,
                PublishedSkill.status == "published"
            )
        )

        # 可扩展：添加分类过滤条件

        result = await self.db.execute(query)
        skills = result.scalars().all()

        # 计算热度并排序
        skill_scores = []
        for skill in skills:
            score = await self.calculate_popularity_score(
                skill_id=skill.id,
                download_count=skill.download_count,
                install_count=skill.install_count,
                rating=skill.rating,
                rating_count=skill.rating_count,
                published_at=skill.published_at,
                updated_at=skill.updated_at
            )
            skill_scores.append({
                "id": skill.id,
                "name": skill.name,
                "slug": skill.slug,
                "popularity_score": score,
                "download_count": skill.download_count,
                "install_count": skill.install_count,
                "rating": float(skill.rating)
            })

        # 按热度排序
        skill_scores.sort(key=lambda x: x["popularity_score"], reverse=True)
        top_skills = skill_scores[:limit]

        # 缓存结果
        await cache.set(cache_key, top_skills, expire=CacheExpire.MEDIUM)

        return top_skills

    async def update_stats_on_download(
        self,
        skill_id: int,
        package_id: Optional[int] = None
    ) -> bool:
        """
        下载时更新统计

        Args:
            skill_id: 技能ID
            package_id: 包ID

        Returns:
            bool: 是否成功
        """
        try:
            # 更新技能下载计数
            await self.db.execute(
                update(PublishedSkill)
                .where(PublishedSkill.id == skill_id)
                .values(download_count=PublishedSkill.download_count + 1)
            )

            # 更新包下载计数
            if package_id:
                await self.db.execute(
                    update(SkillPackage)
                    .where(SkillPackage.id == package_id)
                    .values(download_count=SkillPackage.download_count + 1)
                )

            await self.db.commit()

            # 清除相关缓存
            await cache.delete_pattern(f"skill:detail:{skill_id}*")
            await cache.delete_pattern("skills:top:*")

            return True
        except Exception as e:
            logger.error(f"Failed to update download stats: {e}")
            await self.db.rollback()
            return False

    async def update_stats_on_install(self, skill_id: int) -> bool:
        """
        安装时更新统计

        Args:
            skill_id: 技能ID

        Returns:
            bool: 是否成功
        """
        try:
            await self.db.execute(
                update(PublishedSkill)
                .where(PublishedSkill.id == skill_id)
                .values(install_count=PublishedSkill.install_count + 1)
            )

            await self.db.commit()

            # 清除相关缓存
            await cache.delete_pattern(f"skill:detail:{skill_id}*")

            return True
        except Exception as e:
            logger.error(f"Failed to update install stats: {e}")
            await self.db.rollback()
            return False

    async def update_stats_on_rating(
        self,
        skill_id: int,
        new_rating: int,
        old_rating: Optional[int] = None
    ) -> bool:
        """
        评价时更新统计

        Args:
            skill_id: 技能ID
            new_rating: 新评分
            old_rating: 旧评分（如果是更新评价）

        Returns:
            bool: 是否成功
        """
        try:
            # 获取当前统计
            result = await self.db.execute(
                select(PublishedSkill).where(PublishedSkill.id == skill_id)
            )
            skill = result.scalar_one_or_none()
            if not skill:
                return False

            current_rating = float(skill.rating or 0)
            current_count = skill.rating_count or 0

            if old_rating is None:
                # 新评价
                new_count = current_count + 1
                new_avg = (current_rating * current_count + new_rating) / new_count
            else:
                # 更新评价
                if current_count > 0:
                    new_avg = (current_rating * current_count - old_rating + new_rating) / current_count
                else:
                    new_avg = new_rating
                new_count = current_count

            # 更新
            await self.db.execute(
                update(PublishedSkill)
                .where(PublishedSkill.id == skill_id)
                .values(
                    rating=round(new_avg, 2),
                    rating_count=new_count
                )
            )

            await self.db.commit()

            # 清除相关缓存
            await cache.delete_pattern(f"skill:detail:{skill_id}*")

            return True
        except Exception as e:
            logger.error(f"Failed to update rating stats: {e}")
            await self.db.rollback()
            return False

    async def get_stats_summary(self) -> Dict[str, Any]:
        """
        获取统计摘要

        Returns:
            Dict: 统计摘要
        """
        # 总数统计
        total_query = select(func.count()).select_from(PublishedSkill).where(
            PublishedSkill.status == "published"
        )
        total_result = await self.db.execute(total_query)
        total_skills = total_result.scalar()

        # 下载量统计
        download_query = select(
            func.sum(PublishedSkill.download_count).label("total"),
            func.avg(PublishedSkill.download_count).label("avg")
        ).where(PublishedSkill.status == "published")
        download_result = await self.db.execute(download_query)
        download_row = download_result.first()

        # 评分统计
        rating_query = select(func.avg(PublishedSkill.rating)).where(
            and_(
                PublishedSkill.status == "published",
                PublishedSkill.rating > 0
            )
        )
        rating_result = await self.db.execute(rating_query)
        avg_rating = rating_result.scalar()

        return {
            "total_skills": total_skills,
            "total_downloads": download_row.total or 0,
            "avg_downloads": float(download_row.avg or 0),
            "avg_rating": float(avg_rating or 0),
            "updated_at": datetime.utcnow().isoformat()
        }
