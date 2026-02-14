"""
API限流中间件
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Tuple
import time
from collections import defaultdict


class RateLimiter:
    """简单的内存限流器（生产环境应使用 Redis）"""

    def __init__(self):
        # 存储格式: {key: [(timestamp, count), ...]}
        self.requests: Dict[str, list] = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """
        检查是否允许请求

        Args:
            key: 限流键（通常是 user_id 或 IP）
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）

        Returns:
            (is_allowed, remaining_seconds)
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
            return False, max(0, remaining)

        # 记录本次请求
        self.requests[key].append((now, 1))
        return True, 0


# 全局限流器实例
rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """
    限流中间件

    限流规则：
    - 普通用户: 100 请求/分钟
    - API路由: 60 请求/分钟
    - 文件上传: 10 请求/分钟
    """
    # 跳过健康检查和文档
    if request.url.path in ["/health", "/docs", "/openapi.json"]:
        return await call_next(request)

    # 获取限流键（优先使用用户ID，否则使用IP）
    user_id = getattr(request.state, "user_id", None)
    key = f"user:{user_id}" if user_id else f"ip:{request.client.host}"

    # 根据路由选择限流规则
    if request.url.path.startswith("/files/upload"):
        max_requests, window = 10, 60  # 文件上传: 10次/分钟
    elif request.url.path.startswith("/api/"):
        max_requests, window = 60, 60  # API路由: 60次/分钟
    else:
        max_requests, window = 100, 60  # 默认: 100次/分钟

    # 检查限流
    allowed, remaining = rate_limiter.is_allowed(key, max_requests, window)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {remaining} seconds.",
            headers={"Retry-After": str(remaining)}
        )

    # 添加限流头
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(max_requests)
    response.headers["X-RateLimit-Remaining"] = str(max_requests - len(rate_limiter.requests[key]))

    return response
