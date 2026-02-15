"""
Redis缓存模块

提供高性能的缓存层，减少数据库查询
"""
import json
import hashlib
from typing import Optional, Any, List, Callable
from datetime import timedelta
from functools import wraps
import redis.asyncio as redis
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis缓存管理器"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self):
        """连接到Redis"""
        try:
            self.client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # 测试连接
            await self.client.ping()
            self._connected = True
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Cache will be disabled.")
            self._connected = False
    
    async def disconnect(self):
        """断开Redis连接"""
        if self.client:
            await self.client.close()
            self._connected = False
            logger.info("Disconnected from Redis cache")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        # 将参数转换为字符串并生成哈希
        key_parts = [prefix]
        
        for arg in args:
            key_parts.append(str(arg))
        
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        key_string = "|".join(key_parts)
        
        # 如果键太长，使用哈希
        if len(key_string) > 200:
            hash_obj = hashlib.md5(key_string.encode())
            return f"{prefix}:hash:{hash_obj.hexdigest()}"
        
        return key_string
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self._connected or not self.client:
            return None
        
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        if not self._connected or not self.client:
            return False
        
        try:
            serialized = json.dumps(value)
            if expire:
                await self.client.setex(key, expire, serialized)
            else:
                await self.client.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._connected or not self.client:
            return False
        
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的所有键"""
        if not self._connected or not self.client:
            return 0
        
        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await self.client.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete_pattern error for pattern {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._connected or not self.client:
            return False
        
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def clear_all(self) -> bool:
        """清空所有缓存"""
        if not self._connected or not self.client:
            return False
        
        try:
            await self.client.flushdb()
            logger.info("All cache cleared")
            return True
        except Exception as e:
            logger.error(f"Cache clear_all error: {e}")
            return False


# 全局缓存管理器实例
cache = CacheManager()


# 缓存装饰器
def cached(
    prefix: str,
    expire: int = 300,  # 默认5分钟
    key_builder: Optional[Callable] = None
):
    """
    缓存装饰器
    
    Args:
        prefix: 缓存键前缀
        expire: 过期时间（秒）
        key_builder: 自定义键构建函数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_builder:
                cache_key = key_builder(prefix, *args, **kwargs)
            else:
                # 跳过 self/db 等参数
                cache_args = args[1:] if len(args) > 0 and hasattr(args[0], '__class__') else args
                cache_key = cache._generate_key(prefix, *cache_args, **kwargs)
            
            # 尝试从缓存获取
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            if result is not None:
                await cache.set(cache_key, result, expire)
                logger.debug(f"Cache set for key: {cache_key}")
            
            return result
        
        return wrapper
    return decorator


# 缓存失效装饰器
def invalidate_cache(pattern: str):
    """
    缓存失效装饰器
    
    Args:
        pattern: 要删除的缓存键模式
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 删除相关缓存
            deleted = await cache.delete_pattern(pattern)
            if deleted > 0:
                logger.info(f"Invalidated {deleted} cache entries matching pattern: {pattern}")
            
            return result
        
        return wrapper
    return decorator


# 预定义的缓存键和过期时间
class CacheKeys:
    """缓存键常量"""
    
    # 用户相关
    USER_PROFILE = "user:profile"
    USER_PERMISSIONS = "user:permissions"
    USER_SESSIONS = "user:sessions"
    
    # 技能相关
    SKILL_DETAIL = "skill:detail"
    SKILL_LIST = "skill:list"
    SKILL_SEARCH = "skill:search"
    SKILL_VERSIONS = "skill:versions"
    
    # 会话相关
    SESSION_DETAIL = "session:detail"
    SESSION_MESSAGES = "session:messages"
    
    # 文件相关
    FILE_LIST = "file:list"
    FILE_CONTENT = "file:content"


class CacheExpire:
    """缓存过期时间常量（秒）"""
    
    SHORT = 60  # 1分钟
    MEDIUM = 300  # 5分钟
    LONG = 3600  # 1小时
    VERY_LONG = 86400  # 1天
