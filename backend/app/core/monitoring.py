"""
监控和日志模块

实现：
- API性能监控
- 错误日志收集
- 慢查询检测
"""
import time
import logging
import json
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict
import asyncio

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.cache import cache

logger = logging.getLogger(__name__)


# ============= 性能监控 =============

class PerformanceMonitor:
    """API性能监控"""

    # 性能阈值配置
    SLOW_REQUEST_THRESHOLD_MS = 1000  # 慢请求阈值（毫秒）
    VERY_SLOW_REQUEST_THRESHOLD_MS = 5000  # 非常慢请求阈值

    # 统计数据
    _stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "total_requests": 0,
        "total_time_ms": 0,
        "error_count": 0,
        "slow_count": 0,
        "last_updated": None
    })

    @classmethod
    async def record_request(
        cls,
        endpoint: str,
        method: str,
        duration_ms: float,
        status_code: int,
        error: Optional[str] = None
    ):
        """记录请求性能"""
        key = f"{method}:{endpoint}"
        stats = cls._stats[key]

        stats["total_requests"] += 1
        stats["total_time_ms"] += duration_ms
        stats["last_updated"] = datetime.utcnow().isoformat()

        if status_code >= 400:
            stats["error_count"] += 1

        if duration_ms > cls.SLOW_REQUEST_THRESHOLD_MS:
            stats["slow_count"] += 1

        # 记录到Redis
        if cache._connected and cache.client:
            try:
                # 记录到时间序列
                today = datetime.utcnow().strftime("%Y-%m-%d")
                hour = datetime.utcnow().strftime("%H")

                # 端点性能统计
                await cache.client.hset(
                    f"monitor:api:{today}",
                    f"{key}:count",
                    stats["total_requests"]
                )
                await cache.client.hset(
                    f"monitor:api:{today}",
                    f"{key}:time",
                    stats["total_time_ms"]
                )

                # 记录慢请求
                if duration_ms > cls.SLOW_REQUEST_THRESHOLD_MS:
                    slow_log = {
                        "endpoint": endpoint,
                        "method": method,
                        "duration_ms": duration_ms,
                        "status_code": status_code,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await cache.client.lpush(
                        f"monitor:slow:{today}",
                        json.dumps(slow_log)
                    )
                    # 保留最近1000条
                    await cache.client.ltrim(f"monitor:slow:{today}", 0, 999)

            except Exception as e:
                logger.error(f"Failed to record performance to Redis: {e}")

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """获取性能统计"""
        result = {}
        for key, stats in cls._stats.items():
            if stats["total_requests"] > 0:
                result[key] = {
                    "total_requests": stats["total_requests"],
                    "avg_time_ms": round(stats["total_time_ms"] / stats["total_requests"], 2),
                    "error_count": stats["error_count"],
                    "error_rate": round(stats["error_count"] / stats["total_requests"] * 100, 2),
                    "slow_count": stats["slow_count"],
                    "slow_rate": round(stats["slow_count"] / stats["total_requests"] * 100, 2),
                    "last_updated": stats["last_updated"]
                }
        return result

    @classmethod
    async def get_slow_requests(
        cls,
        date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取慢请求列表"""
        if not cache._connected or not cache.client:
            return []

        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        try:
            logs = await cache.client.lrange(f"monitor:slow:{date}", 0, limit - 1)
            return [json.loads(log) for log in logs]
        except Exception as e:
            logger.error(f"Failed to get slow requests: {e}")
            return []

    @classmethod
    async def get_daily_stats(cls, date: Optional[str] = None) -> Dict[str, Any]:
        """获取每日统计"""
        if not cache._connected or not cache.client:
            return {}

        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        try:
            data = await cache.client.hgetall(f"monitor:api:{date}")
            return data or {}
        except Exception as e:
            logger.error(f"Failed to get daily stats: {e}")
            return {}


# ============= 错误日志收集 =============

class ErrorLogger:
    """错误日志收集器"""

    _errors: List[Dict[str, Any]] = []

    @classmethod
    async def log_error(
        cls,
        error_type: str,
        message: str,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        user_id: Optional[int] = None,
        stack_trace: Optional[str] = None,
        request_data: Optional[Dict] = None
    ):
        """记录错误"""
        error_log = {
            "error_type": error_type,
            "message": message,
            "endpoint": endpoint,
            "method": method,
            "user_id": user_id,
            "stack_trace": stack_trace,
            "request_data": request_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # 内存中保留最近100条
        cls._errors.append(error_log)
        if len(cls._errors) > 100:
            cls._errors = cls._errors[-100:]

        # 记录到Redis
        if cache._connected and cache.client:
            try:
                today = datetime.utcnow().strftime("%Y-%m-%d")
                await cache.client.lpush(
                    f"monitor:errors:{today}",
                    json.dumps(error_log)
                )
                # 保留最近1000条
                await cache.client.ltrim(f"monitor:errors:{today}", 0, 999)

                # 增加错误计数
                await cache.client.incr(f"monitor:errors:{today}:count")
            except Exception as e:
                logger.error(f"Failed to log error to Redis: {e}")

        # 同时记录到日志
        logger.error(
            f"API Error: {error_type} - {message}",
            extra={
                "endpoint": endpoint,
                "method": method,
                "user_id": user_id
            }
        )

    @classmethod
    async def get_recent_errors(
        cls,
        date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取最近错误"""
        if not cache._connected or not cache.client:
            return cls._errors[-limit:]

        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        try:
            logs = await cache.client.lrange(f"monitor:errors:{date}", 0, limit - 1)
            return [json.loads(log) for log in logs]
        except Exception as e:
            logger.error(f"Failed to get errors: {e}")
            return cls._errors[-limit:]

    @classmethod
    async def get_error_count(cls, date: Optional[str] = None) -> int:
        """获取错误计数"""
        if not cache._connected or not cache.client:
            return len(cls._errors)

        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        try:
            count = await cache.client.get(f"monitor:errors:{date}:count")
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Failed to get error count: {e}")
            return 0


# ============= 慢查询检测 =============

class SlowQueryDetector:
    """慢查询检测器"""

    SLOW_QUERY_THRESHOLD_MS = 500  # 慢查询阈值（毫秒）

    @classmethod
    async def log_query(
        cls,
        query: str,
        duration_ms: float,
        params: Optional[Dict] = None
    ):
        """记录查询"""
        if duration_ms < cls.SLOW_QUERY_THRESHOLD_MS:
            return

        query_log = {
            "query": query[:500] if len(query) > 500 else query,  # 截断长查询
            "duration_ms": round(duration_ms, 2),
            "params": params,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.warning(
            f"Slow query detected: {duration_ms:.2f}ms",
            extra={"query": query[:200]}
        )

        # 记录到Redis
        if cache._connected and cache.client:
            try:
                today = datetime.utcnow().strftime("%Y-%m-%d")
                await cache.client.lpush(
                    f"monitor:slow_queries:{today}",
                    json.dumps(query_log)
                )
                await cache.client.ltrim(f"monitor:slow_queries:{today}", 0, 499)

                # 增加慢查询计数
                await cache.client.incr(f"monitor:slow_queries:{today}:count")
            except Exception as e:
                logger.error(f"Failed to log slow query: {e}")

    @classmethod
    async def get_slow_queries(
        cls,
        date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取慢查询列表"""
        if not cache._connected or not cache.client:
            return []

        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        try:
            logs = await cache.client.lrange(f"monitor:slow_queries:{date}", 0, limit - 1)
            return [json.loads(log) for log in logs]
        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            return []

    @classmethod
    async def get_slow_query_count(cls, date: Optional[str] = None) -> int:
        """获取慢查询计数"""
        if not cache._connected or not cache.client:
            return 0

        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        try:
            count = await cache.client.get(f"monitor:slow_queries:{date}:count")
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Failed to get slow query count: {e}")
            return 0


# ============= 监控中间件 =============

class MonitoringMiddleware(BaseHTTPMiddleware):
    """监控中间件"""

    async def dispatch(self, request: Request, call_next):
        # 排除健康检查等路径
        if request.url.path in ["/health", "/metrics", "/"]:
            return await call_next(request)

        start_time = time.time()
        error = None

        try:
            response = await call_next(request)
        except Exception as e:
            error = str(e)
            await ErrorLogger.log_error(
                error_type=type(e).__name__,
                message=str(e),
                endpoint=request.url.path,
                method=request.method
            )
            raise

        # 计算响应时间
        duration_ms = (time.time() - start_time) * 1000

        # 记录性能
        await PerformanceMonitor.record_request(
            endpoint=request.url.path,
            method=request.method,
            duration_ms=duration_ms,
            status_code=response.status_code,
            error=error
        )

        # 添加性能头
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        # 记录慢请求日志
        if duration_ms > PerformanceMonitor.SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} took {duration_ms:.2f}ms"
            )

        return response


# ============= 查询监控装饰器 =============

def monitor_query(func):
    """查询监控装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            # 记录慢查询
            await SlowQueryDetector.log_query(
                query=func.__name__,
                duration_ms=duration_ms,
                params=kwargs if kwargs else None
            )

            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            await ErrorLogger.log_error(
                error_type=type(e).__name__,
                message=str(e),
                endpoint=func.__name__,
                stack_trace=str(e.__traceback__) if hasattr(e, '__traceback__') else None
            )
            raise

    return wrapper


# ============= 监控API响应模型 =============

class MonitoringStats:
    """监控统计数据"""

    @staticmethod
    async def get_full_stats() -> Dict[str, Any]:
        """获取完整监控统计"""
        today = datetime.utcnow().strftime("%Y-%m-%d")

        performance_stats = PerformanceMonitor.get_stats()
        slow_requests = await PerformanceMonitor.get_slow_requests(today, limit=20)
        error_count = await ErrorLogger.get_error_count(today)
        recent_errors = await ErrorLogger.get_recent_errors(today, limit=20)
        slow_query_count = await SlowQueryDetector.get_slow_query_count(today)
        slow_queries = await SlowQueryDetector.get_slow_queries(today, limit=20)

        return {
            "date": today,
            "performance": {
                "endpoints": performance_stats,
                "slow_requests": slow_requests
            },
            "errors": {
                "count": error_count,
                "recent": recent_errors
            },
            "queries": {
                "slow_count": slow_query_count,
                "slow_queries": slow_queries
            },
            "thresholds": {
                "slow_request_ms": PerformanceMonitor.SLOW_REQUEST_THRESHOLD_MS,
                "slow_query_ms": SlowQueryDetector.SLOW_QUERY_THRESHOLD_MS
            }
        }
