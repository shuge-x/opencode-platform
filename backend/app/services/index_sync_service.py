"""
索引同步服务

负责同步技能数据到搜索索引
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
import json
import logging
import asyncio

from app.models.published_skill import PublishedSkill, SkillPackage
from app.models.category import SkillCategory, SkillCategoryMapping
from app.core.cache import cache, CacheKeys, CacheExpire

logger = logging.getLogger(__name__)


class IndexSyncService:
    """索引同步服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._elasticsearch_available = False  # TODO: 检测 Elasticsearch

    async def index_skill(self, skill_id: int) -> bool:
        """
        索引单个技能

        Args:
            skill_id: 技能ID

        Returns:
            bool: 是否成功
        """
        try:
            # 获取技能数据
            result = await self.db.execute(
                select(PublishedSkill).where(PublishedSkill.id == skill_id)
            )
            skill = result.scalar_one_or_none()

            if not skill:
                logger.warning(f"Skill {skill_id} not found for indexing")
                return False

            # 构建索引文档
            doc = await self._build_index_document(skill)

            if self._elasticsearch_available:
                # TODO: 同步到 Elasticsearch
                pass
            else:
                # 使用 PostgreSQL 全文搜索，数据已经在数据库中
                # 只需要清除缓存
                await self._invalidate_cache(skill_id)

            logger.info(f"Indexed skill {skill_id}: {skill.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to index skill {skill_id}: {e}")
            return False

    async def index_skills_batch(
        self,
        skill_ids: Optional[List[int]] = None,
        batch_size: int = 100
    ) -> Dict[str, int]:
        """
        批量索引技能

        Args:
            skill_ids: 指定技能ID列表，如果为None则索引所有
            batch_size: 批处理大小

        Returns:
            Dict: 索引统计
        """
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0
        }

        query = select(PublishedSkill).where(
            PublishedSkill.status == "published"
        )

        if skill_ids:
            query = query.where(PublishedSkill.id.in_(skill_ids))

        result = await self.db.execute(query)
        skills = result.scalars().all()

        stats["total"] = len(skills)

        for i, skill in enumerate(skills):
            success = await self.index_skill(skill.id)
            if success:
                stats["success"] += 1
            else:
                stats["failed"] += 1

            # 批量处理
            if (i + 1) % batch_size == 0:
                logger.info(f"Indexed {i + 1}/{stats['total']} skills")
                await asyncio.sleep(0)  # 让出控制权

        return stats

    async def remove_from_index(self, skill_id: int) -> bool:
        """
        从索引中移除技能

        Args:
            skill_id: 技能ID

        Returns:
            bool: 是否成功
        """
        try:
            if self._elasticsearch_available:
                # TODO: 从 Elasticsearch 删除
                pass

            # 清除缓存
            await self._invalidate_cache(skill_id)

            logger.info(f"Removed skill {skill_id} from index")
            return True

        except Exception as e:
            logger.error(f"Failed to remove skill {skill_id} from index: {e}")
            return False

    async def rebuild_index(
        self,
        clear_existing: bool = True,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        重建搜索索引

        Args:
            clear_existing: 是否清除现有索引
            batch_size: 批处理大小

        Returns:
            Dict: 重建统计
        """
        logger.info("Starting index rebuild...")

        start_time = datetime.utcnow()

        if clear_existing:
            # 清除缓存
            if cache._connected:
                await cache.delete_pattern(f"{CacheKeys.SKILL_SEARCH}:*")
                await cache.delete_pattern("skills:popularity")
                logger.info("Cleared existing cache")

        # 批量索引
        stats = await self.index_skills_batch(batch_size=batch_size)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        result = {
            **stats,
            "duration_seconds": duration,
            "started_at": start_time.isoformat(),
            "finished_at": end_time.isoformat()
        }

        logger.info(f"Index rebuild completed: {result}")
        return result

    async def _build_index_document(self, skill: PublishedSkill) -> Dict[str, Any]:
        """
        构建索引文档

        Args:
            skill: 技能对象

        Returns:
            Dict: 索引文档
        """
        # 获取分类
        categories = await self._get_skill_categories(skill.id)

        # 获取最新版本
        latest_version = await self._get_latest_version(skill.id)

        doc = {
            "id": skill.id,
            "name": skill.name,
            "slug": skill.slug,
            "description": skill.description,
            "version": skill.version,
            "categories": categories,
            "tags": skill.tags or [],
            "price": float(skill.price or 0),
            "currency": skill.currency,
            "status": skill.status,
            "is_public": skill.is_public,
            "is_featured": skill.is_featured,
            "download_count": skill.download_count,
            "install_count": skill.install_count,
            "rating": float(skill.rating or 0),
            "rating_count": skill.rating_count,
            "publisher_id": skill.publisher_id,
            "license": skill.license,
            "published_at": skill.published_at.isoformat() if skill.published_at else None,
            "updated_at": skill.updated_at.isoformat() if skill.updated_at else None,
            "latest_version": latest_version
        }

        return doc

    async def _get_skill_categories(self, skill_id: int) -> List[Dict[str, Any]]:
        """获取技能的分类列表"""
        query = select(SkillCategory).join(
            SkillCategoryMapping,
            SkillCategory.id == SkillCategoryMapping.category_id
        ).where(
            SkillCategoryMapping.published_skill_id == skill_id
        )

        result = await self.db.execute(query)
        categories = result.scalars().all()

        return [
            {"id": cat.id, "name": cat.name, "slug": cat.slug}
            for cat in categories
        ]

    async def _get_latest_version(self, skill_id: int) -> Optional[Dict[str, Any]]:
        """获取技能的最新版本信息"""
        query = select(SkillPackage).where(
            and_(
                SkillPackage.published_skill_id == skill_id,
                SkillPackage.is_latest == True,
                SkillPackage.is_active == True
            )
        )

        result = await self.db.execute(query)
        pkg = result.scalar_one_or_none()

        if pkg:
            return {
                "version": pkg.version,
                "file_size": pkg.file_size,
                "published_at": pkg.published_at.isoformat() if pkg.published_at else None
            }

        return None

    async def _invalidate_cache(self, skill_id: int):
        """清除技能相关缓存"""
        patterns = [
            f"{CacheKeys.SKILL_DETAIL}:{skill_id}",
            f"{CacheKeys.SKILL_LIST}:*",
            f"{CacheKeys.SKILL_SEARCH}:*",
            "skills:top:*",
            "skills:popular:*"
        ]

        for pattern in patterns:
            await cache.delete_pattern(pattern)

    async def sync_on_publish(self, skill_id: int):
        """
        技能发布时的同步钩子

        Args:
            skill_id: 技能ID
        """
        logger.info(f"Syncing index on publish for skill {skill_id}")
        await self.index_skill(skill_id)

    async def sync_on_update(self, skill_id: int):
        """
        技能更新时的同步钩子

        Args:
            skill_id: 技能ID
        """
        logger.info(f"Syncing index on update for skill {skill_id}")
        await self.index_skill(skill_id)

    async def sync_on_delete(self, skill_id: int):
        """
        技能删除时的同步钩子

        Args:
            skill_id: 技能ID
        """
        logger.info(f"Syncing index on delete for skill {skill_id}")
        await self.remove_from_index(skill_id)

    async def sync_on_status_change(self, skill_id: int, new_status: str):
        """
        技能状态变更时的同步钩子

        Args:
            skill_id: 技能ID
            new_status: 新状态
        """
        if new_status == "published":
            await self.index_skill(skill_id)
        elif new_status in ("deprecated", "rejected"):
            await self.remove_from_index(skill_id)
