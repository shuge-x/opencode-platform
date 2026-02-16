"""
API限流中间件 - 支持 Redis 和内存双模式
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Tuple, Optional
import time
import logging
from collections import defaultdict

from app.core.cache import cache
from app.config import settings

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """内存限流器（Redis 不可用时的后备方案）"""

    def __init__(self):
        # 存储格式: {key: [(timestamp, count), ...]}
        self.requests: Dict[str, list] = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int, int]:
        """
        检查是否允许请求

        Args:
            key: 限流键（通常是 user_id 或 IP）
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）

        Returns:
            (is_allowed, remaining_seconds, current_count)
        """
        now = time.time()
        window_start = now - window_seconds

        # 清理过期的请求记录
        self.requests[key] = [
            (ts, count) for ts, count in self.requests[key]
            if ts > window_start
        ]

        # 计算当前窗口内的请求数
        current_count = sum(count for _, count in self.requests[key])

        if current_count >= max_requests:
            # 计算需要等待的时间
            oldest_ts = min(ts for ts, _ in self.requests[key])
            remaining = int(oldest_ts + window_seconds - now)
            return False, max(0, remaining), current_count

        # 记录本次请求
        self.requests[key].append((now, 1))
        return True, 0, current_count + 1


class RedisRateLimiter:
    """Redis 限流器（使用滑动窗口算法）"""

    def __init__(self):
        self.key_prefix = "ratelimit"

    async def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int, int]:
        """
        使用 Redis 实现滑动窗口限流

        Args:
            key: 限流键
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）

        Returns:
            (is_allowed, remaining_seconds, current_count)
        """
        if not cache._connected or not cache.client:
            # Redis 不可用，返回允许（由外层使用后备方案）
            raise ConnectionError("Redis not connected")

        redis_key = f"{self.key_prefix}:{key}"
        now = time.time()
        window_start = now - window_seconds

        try:
            # 使用 Redis 事务确保原子性
            async with cache.client.pipeline() as pipe:
                # 1. 移除过期的请求记录
                await pipe.zremrangebyscore(redis_key, 0, window_start)
                
                # 2. 获取当前窗口内的请求数
                await pipe.zcard(redis_key)
                
                # 3. 执行事务
                results = await pipe.execute()
                
            current_count = results[1]

            if current_count >= max_requests:
                # 获取最早的请求时间，计算剩余等待时间
                oldest = await cache.client.zrange(redis_key, 0, 0, withscores=True)
                if oldest:
                    oldest_ts = oldest[0][1]
                    remaining = int(oldest_ts + window_seconds - now)
                    return False, max(0, remaining), current_count
                return False, window_seconds, current_count

            # 添加当前请求
            await cache.client.zadd(redis_key, {str(now): now})
            # 设置过期时间
            await cache.client.expire(redis_key, window_seconds + 1)

            return True, 0, current_count + 1

        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            raise


class RateLimiter:
    """智能限流器 - 优先使用 Redis，降级到内存"""

    def __init__(self):
        self.redis_limiter = RedisRateLimiter()
        self.memory_limiter = InMemoryRateLimiter()
        self._use_redis = True

    async def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int, int]:
        """
        检查是否允许请求

        Args:
            key: 限流键
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）

        Returns:
            (is_allowed, remaining_seconds, current_count)
        """
        # 尝试使用 Redis
        if self._use_redis and cache._connected:
            try:
                return await self.redis_limiter.is_allowed(key, max_requests, window_seconds)
            except (ConnectionError, Exception) as e:
                logger.warning(f"Redis rate limit failed, falling back to memory: {e}")
                self._use_redis = False

        # 使用内存限流器
        return self.memory_limiter.is_allowed(key, max_requests, window_seconds)

    def reset_redis_flag(self):
        """重置 Redis 可用标志（允许再次尝试 Redis）"""
        self._use_redis = True


# 全局限流器实例
rate_limiter = RateLimiter()


# 限流配置
class RateLimitConfig:
    """限流配置"""
    
    # 默认限流规则
    DEFAULT = (100, 60)  # 100 请求/分钟
    
    # API 路由
    API = (60, 60)  # 60 请求/分钟
    
    # 文件上传
    FILE_UPLOAD = (10, 60)  # 10 次/分钟
    
    # 认证相关
    AUTH = (10, 60)  # 10 次/分钟
    
    # WebSocket 连接
    WEBSOCKET = (30, 60)  # 30 次/分钟


async def rate_limit_middleware(request: Request, call_next):
    """
    限流中间件

    限流规则：
    - 普通请求: 100 请求/分钟
    - API路由: 60 请求/分钟
    - 文件上传: 10 请求/分钟
    - 认证接口: 10 请求/分钟
    """
    # 跳过健康检查和文档
    if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)

    # 定期重试 Redis 连接
    if not rate_limiter._use_redis and cache._connected:
        rate_limiter.reset_redis_flag()

    # 获取限流键（优先使用用户ID，否则使用IP）
    user_id = getattr(request.state, "user_id", None)
    client_ip = request.client.host if request.client else "unknown"
    
    # 处理代理情况
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    key = f"user:{user_id}" if user_id else f"ip:{client_ip}"

    # 根据路由选择限流规则
    if "/upload" in request.url.path:
        max_requests, window = RateLimitConfig.FILE_UPLOAD
    elif "/auth/" in request.url.path or "/login" in request.url.path:
        max_requests, window = RateLimitConfig.AUTH
    elif request.url.path.startswith("/api/"):
        max_requests, window = RateLimitConfig.API
    else:
        max_requests, window = RateLimitConfig.DEFAULT

    # 检查限流
    allowed, remaining, current_count = await rate_limiter.is_allowed(key, max_requests, window)

    if not allowed:
        logger.warning(
            f"Rate limit exceeded: key={key}, path={request.url.path}, "
            f"count={current_count}, limit={max_requests}/window"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {remaining} seconds.",
            headers={"Retry-After": str(remaining)}
        )

    # 执行请求
    response = await call_next(request)
    
    # 添加限流头
    response.headers["X-RateLimit-Limit"] = str(max_requests)
    response.headers["X-RateLimit-Remaining"] = str(max(0, max_requests - current_count))
    response.headers["X-RateLimit-Reset"] = str(window)

    return response
