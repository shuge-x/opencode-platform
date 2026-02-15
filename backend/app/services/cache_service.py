"""
性能缓存服务

实现高性能缓存层，优化：
- 搜索结果缓存
- 热门技能缓存
- API响应缓存
"""
from typing import Optional, List, Dict, Any, Callable
from datetime import timedelta
import json
import hashlib
import logging
import time
from functools import wraps

from app.core.cache import cache, CacheKeys, CacheExpire

logger = logging.getLogger(__name__)


class PerformanceCacheService:
    """性能缓存服务"""

    # 缓存键前缀
    PREFIX_SEARCH = "cache:search"
    PREFIX_HOT_SKILLS = "cache:hot_skills"
    PREFIX_API = "cache:api"
    PREFIX_SKILL_DETAIL = "cache:skill"

    # 缓存过期时间（秒）
    SEARCH_TTL = 300  # 5分钟
    HOT_SKILLS_TTL = 600  # 10分钟
    SKILL_DETAIL_TTL = 300  # 5分钟
    CATEGORY_TTL = 1800  # 30分钟
    API_TTL = 60  # 1分钟

    def __init__(self):
        self.redis = None

    async def init(self):
        """初始化Redis连接"""
        if cache._connected and cache.client:
            self.redis = cache.client

    # ============= 搜索结果缓存 =============

    def _build_search_cache_key(
        self,
        query: Optional[str],
        filters: Dict[str, Any],
        sort_by: str,
        sort_order: str,
        page: int,
        page_size: int
    ) -> str:
        """构建搜索缓存键"""
        filter_str = json.dumps(filters, sort_keys=True)
        key_data = f"{query or ''}|{filter_str}|{sort_by}|{sort_order}|{page}|{page_size}"
        hash_key = hashlib.md5(key_data.encode()).hexdigest()
        return f"{self.PREFIX_SEARCH}:{hash_key}"

    async def get_search_result(
        self,
        query: Optional[str],
        filters: Dict[str, Any],
        sort_by: str,
        sort_order: str,
        page: int,
        page_size: int
    ) -> Optional[Dict[str, Any]]:
        """获取搜索结果缓存"""
        if not self.redis:
            return None

        key = self._build_search_cache_key(query, filters, sort_by, sort_order, page, page_size)
        try:
            data = await self.redis.get(key)
            if data:
                logger.debug(f"Search cache hit: {key}")
                return json.loads(data)
        except Exception as e:
            logger.error(f"Search cache get error: {e}")

        return None

    async def set_search_result(
        self,
        query: Optional[str],
        filters: Dict[str, Any],
        sort_by: str,
        sort_order: str,
        page: int,
        page_size: int,
        result: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """设置搜索结果缓存"""
        if not self.redis:
            return False

        key = self._build_search_cache_key(query, filters, sort_by, sort_order, page, page_size)
        try:
            await self.redis.setex(
                key,
                ttl or self.SEARCH_TTL,
                json.dumps(result)
            )
            logger.debug(f"Search cache set: {key}")
            return True
        except Exception as e:
            logger.error(f"Search cache set error: {e}")
            return False

    async def invalidate_search_cache(self) -> int:
        """清除所有搜索缓存"""
        if not self.redis:
            return 0

        return await cache.delete_pattern(f"{self.PREFIX_SEARCH}:*")

    # ============= 热门技能缓存 =============

    async def get_hot_skills(
        self,
        category_id: Optional[int] = None,
        limit: int = 100
    ) -> Optional[List[Dict[str, Any]]]:
        """获取热门技能缓存"""
        if not self.redis:
            return None

        key = f"{self.PREFIX_HOT_SKILLS}:{category_id or 'all'}:{limit}"
        try:
            data = await self.redis.get(key)
            if data:
                logger.debug(f"Hot skills cache hit: {key}")
                return json.loads(data)
        except Exception as e:
            logger.error(f"Hot skills cache get error: {e}")

        return None

    async def set_hot_skills(
        self,
        skills: List[Dict[str, Any]],
        category_id: Optional[int] = None,
        limit: int = 100,
        ttl: Optional[int] = None
    ) -> bool:
        """设置热门技能缓存"""
        if not self.redis:
            return False

        key = f"{self.PREFIX_HOT_SKILLS}:{category_id or 'all'}:{limit}"
        try:
            await self.redis.setex(
                key,
                ttl or self.HOT_SKILLS_TTL,
                json.dumps(skills)
            )
            logger.debug(f"Hot skills cache set: {key}")
            return True
        except Exception as e:
            logger.error(f"Hot skills cache set error: {e}")
            return False

    async def invalidate_hot_skills_cache(self) -> int:
        """清除所有热门技能缓存"""
        if not self.redis:
            return 0

        return await cache.delete_pattern(f"{self.PREFIX_HOT_SKILLS}:*")

    # ============= 技能详情缓存 =============

    async def get_skill_detail(self, skill_id: int) -> Optional[Dict[str, Any]]:
        """获取技能详情缓存"""
        if not self.redis:
            return None

        key = f"{self.PREFIX_SKILL_DETAIL}:{skill_id}"
        try:
            data = await self.redis.get(key)
            if data:
                logger.debug(f"Skill detail cache hit: {key}")
                return json.loads(data)
        except Exception as e:
            logger.error(f"Skill detail cache get error: {e}")

        return None

    async def set_skill_detail(
        self,
        skill_id: int,
        detail: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """设置技能详情缓存"""
        if not self.redis:
            return False

        key = f"{self.PREFIX_SKILL_DETAIL}:{skill_id}"
        try:
            await self.redis.setex(
                key,
                ttl or self.SKILL_DETAIL_TTL,
                json.dumps(detail)
            )
            logger.debug(f"Skill detail cache set: {key}")
            return True
        except Exception as e:
            logger.error(f"Skill detail cache set error: {e}")
            return False

    async def invalidate_skill_detail(self, skill_id: int) -> bool:
        """清除技能详情缓存"""
        if not self.redis:
            return False

        key = f"{self.PREFIX_SKILL_DETAIL}:{skill_id}"
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Skill detail cache delete error: {e}")
            return False

    # ============= API响应缓存 =============

    def _build_api_cache_key(
        self,
        endpoint: str,
        params: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> str:
        """构建API缓存键"""
        param_str = json.dumps(params, sort_keys=True)
        key_data = f"{endpoint}|{param_str}|user:{user_id or 'anon'}"
        hash_key = hashlib.md5(key_data.encode()).hexdigest()
        return f"{self.PREFIX_API}:{hash_key}"

    async def get_api_response(
        self,
        endpoint: str,
        params: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """获取API响应缓存"""
        if not self.redis:
            return None

        key = self._build_api_cache_key(endpoint, params, user_id)
        try:
            data = await self.redis.get(key)
            if data:
                logger.debug(f"API cache hit: {key}")
                return json.loads(data)
        except Exception as e:
            logger.error(f"API cache get error: {e}")

        return None

    async def set_api_response(
        self,
        endpoint: str,
        params: Dict[str, Any],
        response: Dict[str, Any],
        user_id: Optional[int] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """设置API响应缓存"""
        if not self.redis:
            return False

        key = self._build_api_cache_key(endpoint, params, user_id)
        try:
            await self.redis.setex(
                key,
                ttl or self.API_TTL,
                json.dumps(response)
            )
            logger.debug(f"API cache set: {key}")
            return True
        except Exception as e:
            logger.error(f"API cache set error: {e}")
            return False

    async def invalidate_api_cache(self, pattern: Optional[str] = None) -> int:
        """清除API响应缓存"""
        if not self.redis:
            return 0

        if pattern:
            return await cache.delete_pattern(f"{self.PREFIX_API}:{pattern}*")
        else:
            return await cache.delete_pattern(f"{self.PREFIX_API}:*")

    # ============= 缓存预热 =============

    async def warmup_cache(
        self,
        db,
        warmup_hot_skills: bool = True,
        warmup_categories: bool = True
    ) -> Dict[str, int]:
        """
        缓存预热
        
        预热常用数据到缓存中
        """
        from sqlalchemy import select, func
        from app.models.published_skill import PublishedSkill
        from app.models.category import SkillCategory
        from app.services.popularity_service import PopularityService

        stats = {
            "hot_skills": 0,
            "categories": 0
        }

        # 预热热门技能
        if warmup_hot_skills:
            try:
                popularity_service = PopularityService(db)
                hot_skills = await popularity_service.get_top_skills_by_popularity(limit=100)
                await self.set_hot_skills(hot_skills, limit=100)
                stats["hot_skills"] = len(hot_skills)
                logger.info(f"Warmed up {stats['hot_skills']} hot skills")
            except Exception as e:
                logger.error(f"Failed to warmup hot skills: {e}")

        # 预热分类
        if warmup_categories:
            try:
                result = await db.execute(
                    select(SkillCategory).where(SkillCategory.is_active == True)
                )
                categories = result.scalars().all()
                categories_data = [
                    {
                        "id": c.id,
                        "name": c.name,
                        "slug": c.slug,
                        "skill_count": c.skill_count
                    }
                    for c in categories
                ]
                await cache.set(
                    f"{self.PREFIX_HOT_SKILLS}:categories",
                    categories_data,
                    expire=self.CATEGORY_TTL
                )
                stats["categories"] = len(categories_data)
                logger.info(f"Warmed up {stats['categories']} categories")
            except Exception as e:
                logger.error(f"Failed to warmup categories: {e}")

        return stats

    # ============= 缓存统计 =============

    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if not self.redis:
            return {
                "connected": False,
                "keys": 0,
                "memory_usage": "N/A"
            }

        try:
            info = await self.redis.info("memory")
            dbsize = await self.redis.dbsize()

            return {
                "connected": True,
                "keys": dbsize,
                "memory_usage": info.get("used_memory_human", "N/A"),
                "peak_memory": info.get("used_memory_peak_human", "N/A")
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                "connected": False,
                "error": str(e)
            }


# 全局性能缓存服务实例
perf_cache = PerformanceCacheService()


# 缓存装饰器
def cached_response(
    prefix: str,
    ttl: int = 60,
    key_params: Optional[List[str]] = None
):
    """
    API响应缓存装饰器
    
    Args:
        prefix: 缓存键前缀
        ttl: 过期时间（秒）
        key_params: 用于构建缓存键的参数名列表
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 构建缓存键
            cache_key_parts = [prefix]
            
            if key_params:
                for param in key_params:
                    if param in kwargs:
                        cache_key_parts.append(f"{param}:{kwargs[param]}")
            
            cache_key = ":".join(cache_key_parts)
            
            # 尝试从缓存获取
            cached = await cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            if result is not None:
                await cache.set(cache_key, result, expire=ttl)
                logger.debug(f"Cache set for {cache_key}")
            
            return result
        
        return wrapper
    return decorator
