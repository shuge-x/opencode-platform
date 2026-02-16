"""
搜索服务

提供技能搜索功能，支持：
- PostgreSQL 全文搜索（默认，降级方案）
- Elasticsearch（如果可用）
- Redis 缓存热门搜索
"""
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, text
from sqlalchemy.sql.expression import literal_column
import json
import logging
from datetime import datetime, timedelta

from app.models.published_skill import PublishedSkill, SkillPackage
from app.models.category import SkillCategory, SkillCategoryMapping
from app.core.cache import cache, CacheKeys, CacheExpire
from app.config import settings

logger = logging.getLogger(__name__)


class SearchService:
    """搜索服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.use_elasticsearch = False  # 可配置 Elasticsearch（需要额外检测逻辑）

    async def search_skills(
        self,
        query: Optional[str] = None,
        category_id: Optional[int] = None,
        category_slug: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        is_free: Optional[bool] = None,
        is_featured: Optional[bool] = None,
        publisher_id: Optional[int] = None,
        sort_by: str = "popularity",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
        include_highlights: bool = True
    ) -> Tuple[List[Dict[str, Any]], int, Dict[str, Any]]:
        """
        搜索技能

        Args:
            query: 搜索关键词
            category_id: 分类ID
            category_slug: 分类slug
            tags: 标签列表
            min_rating: 最低评分
            max_rating: 最高评分
            price_min: 最低价格
            price_max: 最高价格
            is_free: 只看免费
            is_featured: 只看精选
            publisher_id: 发布者ID
            sort_by: 排序字段 (popularity, rating, download_count, created_at, name, price)
            sort_order: 排序方向 (asc, desc)
            page: 页码
            page_size: 每页数量
            include_highlights: 是否包含高亮

        Returns:
            Tuple[List[Dict], int, Dict]: (结果列表, 总数, 搜索元数据)
        """
        # 构建基础查询
        base_query = select(PublishedSkill).where(
            and_(
                PublishedSkill.is_public == True,
                PublishedSkill.status == "published"
            )
        )

        # 全文搜索
        if query:
            base_query = await self._apply_fulltext_search(base_query, query)

        # 分类过滤
        if category_id or category_slug:
            base_query = await self._apply_category_filter(
                base_query, category_id=category_id, category_slug=category_slug
            )

        # 标签过滤
        if tags:
            base_query = self._apply_tag_filter(base_query, tags)

        # 评分过滤
        if min_rating is not None:
            base_query = base_query.where(PublishedSkill.rating >= min_rating)
        if max_rating is not None:
            base_query = base_query.where(PublishedSkill.rating <= max_rating)

        # 价格过滤
        if is_free:
            base_query = base_query.where(PublishedSkill.price == 0)
        else:
            if price_min is not None:
                base_query = base_query.where(PublishedSkill.price >= price_min)
            if price_max is not None:
                base_query = base_query.where(PublishedSkill.price <= price_max)

        # 精选过滤
        if is_featured is not None:
            base_query = base_query.where(PublishedSkill.is_featured == is_featured)

        # 发布者过滤
        if publisher_id:
            base_query = base_query.where(PublishedSkill.publisher_id == publisher_id)

        # 计算总数
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # 应用排序
        base_query = self._apply_sorting(base_query, sort_by, sort_order)

        # 分页
        offset = (page - 1) * page_size
        base_query = base_query.offset(offset).limit(page_size)

        # 执行查询
        result = await self.db.execute(base_query)
        skills = result.scalars().all()

        # 转换结果
        items = []
        for skill in skills:
            item = self._skill_to_dict(skill)

            # 添加高亮
            if include_highlights and query:
                item["highlights"] = self._generate_highlights(skill, query)

            items.append(item)

        # 搜索元数据
        metadata = {
            "query": query,
            "filters": {
                "category_id": category_id,
                "category_slug": category_slug,
                "tags": tags,
                "min_rating": min_rating,
                "max_rating": max_rating,
                "is_free": is_free,
                "is_featured": is_featured
            },
            "sort": {"field": sort_by, "order": sort_order},
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
            "took_ms": 0  # 耗时统计（可通过time.monotonic计算）
        }

        return items, total, metadata

    async def _apply_fulltext_search(self, query, search_term: str):
        """应用全文搜索"""
        # 使用 PostgreSQL 全文搜索
        # 创建搜索向量
        search_vector = func.to_tsvector('english',
            func.coalesce(PublishedSkill.name, '') + ' ' +
            func.coalesce(PublishedSkill.description, '')
        )

        # 创建搜索查询
        search_query = func.plainto_tsquery('english', search_term)

        # 添加全文搜索条件
        query = query.where(search_vector.op('@@')(search_query))

        # 添加排名计算
        rank = func.ts_rank(search_vector, search_query)
        query = query.add_columns(rank.label('search_rank'))

        return query

    async def _apply_category_filter(
        self,
        query,
        category_id: Optional[int] = None,
        category_slug: Optional[str] = None
    ):
        """应用分类过滤"""
        if category_slug:
            # 通过 slug 查找分类
            cat_result = await self.db.execute(
                select(SkillCategory.id).where(
                    and_(SkillCategory.slug == category_slug, SkillCategory.is_active == True)
                )
            )
            cat = cat_result.scalar_one_or_none()
            if cat:
                category_id = cat

        if category_id:
            # 子查询获取分类下的技能
            subquery = select(SkillCategoryMapping.published_skill_id).where(
                SkillCategoryMapping.category_id == category_id
            )
            query = query.where(PublishedSkill.id.in_(subquery))

        return query

    def _apply_tag_filter(self, query, tags: List[str]):
        """应用标签过滤"""
        # PostgreSQL JSON 数组查询
        conditions = []
        for tag in tags:
            conditions.append(
                PublishedSkill.tags.contains([tag])
            )
        query = query.where(or_(*conditions))
        return query

    def _apply_sorting(self, query, sort_by: str, sort_order: str):
        """应用排序"""
        # 计算热度分数（如果按热度排序）
        if sort_by == "popularity":
            # 热度分数 = 下载量 * 0.5 + 使用量 * 0.3 + 评分 * 0.2 * 100
            popularity_score = (
                PublishedSkill.download_count * 0.5 +
                PublishedSkill.install_count * 0.3 +
                PublishedSkill.rating * 20  # 评分 0-5 转换为 0-100
            )
            query = query.add_columns(popularity_score.label('popularity_score'))

            if sort_order == "desc":
                query = query.order_by(popularity_score.desc())
            else:
                query = query.order_by(popularity_score.asc())
        else:
            # 其他排序字段
            sort_field_map = {
                "download_count": PublishedSkill.download_count,
                "rating": PublishedSkill.rating,
                "created_at": PublishedSkill.created_at,
                "updated_at": PublishedSkill.updated_at,
                "name": PublishedSkill.name,
                "price": PublishedSkill.price,
                "install_count": PublishedSkill.install_count
            }

            sort_field = sort_field_map.get(sort_by, PublishedSkill.download_count)

            if sort_order == "desc":
                query = query.order_by(sort_field.desc())
            else:
                query = query.order_by(sort_field.asc())

        # 默认二级排序
        if sort_by != "created_at":
            query = query.order_by(PublishedSkill.created_at.desc())

        return query

    def _skill_to_dict(self, skill: PublishedSkill) -> Dict[str, Any]:
        """将技能对象转换为字典"""
        return {
            "id": skill.id,
            "skill_id": skill.skill_id,
            "publisher_id": skill.publisher_id,
            "name": skill.name,
            "slug": skill.slug,
            "description": skill.description,
            "version": skill.version,
            "category": skill.category,
            "tags": skill.tags or [],
            "price": float(skill.price) if skill.price else 0.0,
            "currency": skill.currency,
            "status": skill.status,
            "is_public": skill.is_public,
            "is_featured": skill.is_featured,
            "download_count": skill.download_count,
            "install_count": skill.install_count,
            "rating": float(skill.rating) if skill.rating else 0.0,
            "rating_count": skill.rating_count,
            "homepage_url": skill.homepage_url,
            "repository_url": skill.repository_url,
            "documentation_url": skill.documentation_url,
            "license": skill.license,
            "published_at": skill.published_at.isoformat() if skill.published_at else None,
            "created_at": skill.created_at.isoformat() if skill.created_at else None,
            "updated_at": skill.updated_at.isoformat() if skill.updated_at else None,
        }

    def _generate_highlights(self, skill: PublishedSkill, query: str) -> Dict[str, str]:
        """生成搜索高亮"""
        highlights = {}
        query_lower = query.lower()

        # 名称高亮
        if skill.name and query_lower in skill.name.lower():
            highlights["name"] = self._highlight_text(skill.name, query)

        # 描述高亮（截取相关片段）
        if skill.description and query_lower in skill.description.lower():
            snippet = self._extract_snippet(skill.description, query, 200)
            highlights["description"] = self._highlight_text(snippet, query)

        return highlights

    def _highlight_text(self, text: str, query: str, tag: str = "em") -> str:
        """高亮文本中的查询词"""
        import re
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        return pattern.sub(f"<{tag}>\\g<0></{tag}>", text)

    def _extract_snippet(self, text: str, query: str, max_length: int = 200) -> str:
        """提取包含查询词的文本片段"""
        query_lower = query.lower()
        text_lower = text.lower()

        pos = text_lower.find(query_lower)
        if pos == -1:
            return text[:max_length] + "..." if len(text) > max_length else text

        # 计算片段起始位置
        start = max(0, pos - max_length // 3)
        end = min(len(text), start + max_length)

        snippet = text[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        return snippet

    async def get_search_suggestions(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取搜索建议

        Args:
            query: 输入的前缀
            limit: 返回数量限制

        Returns:
            List[Dict]: 建议列表
        """
        if len(query) < 2:
            return []

        # 尝试从缓存获取
        cache_key = f"{CacheKeys.SKILL_SEARCH}:suggestions:{query}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        suggestions = []

        # 名称建议
        name_query = select(
            PublishedSkill.name,
            PublishedSkill.slug,
            PublishedSkill.download_count
        ).where(
            and_(
                PublishedSkill.is_public == True,
                PublishedSkill.status == "published",
                PublishedSkill.name.ilike(f"{query}%")
            )
        ).order_by(PublishedSkill.download_count.desc()).limit(limit)

        result = await self.db.execute(name_query)
        name_matches = result.all()

        for name, slug, downloads in name_matches:
            suggestions.append({
                "type": "skill",
                "text": name,
                "slug": slug,
                "score": downloads
            })

        # 标签建议
        tag_query = select(PublishedSkill.tags).where(
            and_(
                PublishedSkill.is_public == True,
                PublishedSkill.status == "published",
                PublishedSkill.tags != None
            )
        ).limit(100)

        result = await self.db.execute(tag_query)
        all_tags = result.scalars().all()

        # 收集匹配的标签
        matched_tags = set()
        for tags in all_tags:
            if tags:
                for tag in tags:
                    if tag.lower().startswith(query.lower()):
                        matched_tags.add(tag)

        for tag in sorted(matched_tags, key=lambda t: t.lower())[:5]:
            suggestions.append({
                "type": "tag",
                "text": tag,
                "score": 50
            })

        # 按分数排序
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        suggestions = suggestions[:limit]

        # 缓存结果
        await cache.set(cache_key, suggestions, expire=CacheExpire.SHORT)

        return suggestions

    async def get_popular_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取热门搜索词

        Returns:
            List[Dict]: 热门搜索列表
        """
        cache_key = f"{CacheKeys.SKILL_SEARCH}:popular"

        # 尝试从缓存获取
        cached = await cache.get(cache_key)
        if cached:
            return cached

        # 基于热门技能生成
        query = select(
            PublishedSkill.name,
            PublishedSkill.slug,
            PublishedSkill.download_count
        ).where(
            and_(
                PublishedSkill.is_public == True,
                PublishedSkill.status == "published"
            )
        ).order_by(PublishedSkill.download_count.desc()).limit(limit)

        result = await self.db.execute(query)
        skills = result.all()

        popular = [
            {
                "text": name,
                "slug": slug,
                "count": downloads
            }
            for name, slug, downloads in skills
        ]

        # 缓存结果
        await cache.set(cache_key, popular, expire=CacheExpire.MEDIUM)

        return popular

    async def record_search(self, query: str, results_count: int):
        """
        记录搜索行为（用于统计热门搜索）

        Args:
            query: 搜索词
            results_count: 结果数量
        """
        if not query or len(query) < 2:
            return

        try:
            # 使用 Redis 有序集合记录搜索频率
            if cache._connected and cache.client:
                key = "search:analytics:queries"
                await cache.client.zincrby(key, 1, query.lower())
                # 设置过期时间
                await cache.client.expire(key, CacheExpire.VERY_LONG)
        except Exception as e:
            logger.error(f"Failed to record search: {e}")

    async def get_facets(self) -> Dict[str, Any]:
        """
        获取搜索面（用于筛选）

        Returns:
            Dict: 各维度的统计数据
        """
        cache_key = f"{CacheKeys.SKILL_SEARCH}:facets"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        facets = {}

        # 分类统计
        cat_query = select(
            SkillCategory.id,
            SkillCategory.name,
            SkillCategory.slug,
            func.count(SkillCategoryMapping.id).label("count")
        ).outerjoin(
            SkillCategoryMapping, SkillCategory.id == SkillCategoryMapping.category_id
        ).where(
            SkillCategory.is_active == True
        ).group_by(SkillCategory.id).order_by(func.count(SkillCategoryMapping.id).desc())

        result = await self.db.execute(cat_query)
        facets["categories"] = [
            {"id": row.id, "name": row.name, "slug": row.slug, "count": row.count}
            for row in result.all()
        ]

        # 价格范围
        price_query = select(
            func.min(PublishedSkill.price).label("min"),
            func.max(PublishedSkill.price).label("max")
        ).where(
            and_(
                PublishedSkill.is_public == True,
                PublishedSkill.status == "published"
            )
        )
        result = await self.db.execute(price_query)
        price_row = result.first()
        facets["price_range"] = {
            "min": float(price_row.min) if price_row.min else 0,
            "max": float(price_row.max) if price_row.max else 0
        }

        # 评分分布
        rating_query = select(
            func.floor(PublishedSkill.rating).label("rating_floor"),
            func.count().label("count")
        ).where(
            and_(
                PublishedSkill.is_public == True,
                PublishedSkill.status == "published",
                PublishedSkill.rating > 0
            )
        ).group_by(func.floor(PublishedSkill.rating))

        result = await self.db.execute(rating_query)
        facets["rating_distribution"] = {
            int(row.rating_floor): row.count
            for row in result.all()
        }

        # 缓存结果
        await cache.set(cache_key, facets, expire=CacheExpire.MEDIUM)

        return facets
