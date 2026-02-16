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


# ============= 系统资源监控 =============

class SystemMetrics:
    """系统资源监控"""
    
    _metrics: Dict[str, Any] = {}
    
    @classmethod
    async def collect(cls) -> Dict[str, Any]:
        """收集系统指标"""
        import psutil
        import os
        
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            
            # 内存使用
            memory = psutil.virtual_memory()
            
            # 磁盘使用
            disk = psutil.disk_usage('/')
            
            # 进程信息
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info()
            
            # 网络连接数
            connections = len(psutil.net_connections())
            
            cls._metrics = {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "load_avg": list(os.getloadavg()) if hasattr(os, 'getloadavg') else None
                },
                "memory": {
                    "total_mb": round(memory.total / (1024 * 1024), 2),
                    "available_mb": round(memory.available / (1024 * 1024), 2),
                    "used_mb": round(memory.used / (1024 * 1024), 2),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
                    "used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
                    "free_gb": round(disk.free / (1024 * 1024 * 1024), 2),
                    "percent": disk.percent
                },
                "process": {
                    "rss_mb": round(process_memory.rss / (1024 * 1024), 2),
                    "vms_mb": round(process_memory.vms / (1024 * 1024), 2),
                    "open_files": len(process.open_files()) if hasattr(process, 'open_files') else 0,
                    "threads": process.num_threads()
                },
                "network": {
                    "connections": connections
                }
            }
            
            return cls._metrics
        except ImportError:
            # psutil 未安装
            return {"error": "psutil not installed"}
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {"error": str(e)}
    
    @classmethod
    def get_cached(cls) -> Dict[str, Any]:
        """获取缓存的系统指标"""
        return cls._metrics


# ============= 技能执行指标 =============

class SkillExecutionMetrics:
    """技能执行指标"""
    
    _stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "total_executions": 0,
        "success_count": 0,
        "failure_count": 0,
        "timeout_count": 0,
        "total_time_ms": 0,
        "last_executed": None
    })
    
    @classmethod
    async def record_execution(
        cls,
        skill_id: int,
        success: bool,
        execution_time_ms: int,
        error_code: Optional[str] = None
    ):
        """记录技能执行"""
        key = f"skill:{skill_id}"
        stats = cls._stats[key]
        
        stats["total_executions"] += 1
        stats["total_time_ms"] += execution_time_ms
        stats["last_executed"] = datetime.utcnow().isoformat()
        
        if success:
            stats["success_count"] += 1
        else:
            stats["failure_count"] += 1
            if error_code == "TIMEOUT":
                stats["timeout_count"] += 1
        
        # 记录到 Redis
        if cache._connected and cache.client:
            try:
                today = datetime.utcnow().strftime("%Y-%m-%d")
                await cache.client.hincrby(f"monitor:skills:{today}", f"{skill_id}:total", 1)
                if success:
                    await cache.client.hincrby(f"monitor:skills:{today}", f"{skill_id}:success", 1)
                else:
                    await cache.client.hincrby(f"monitor:skills:{today}", f"{skill_id}:failure", 1)
            except Exception as e:
                logger.error(f"Failed to record skill execution: {e}")
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """获取技能执行统计"""
        result = {}
        for key, stats in cls._stats.items():
            if stats["total_executions"] > 0:
                result[key] = {
                    "total_executions": stats["total_executions"],
                    "success_rate": round(
                        stats["success_count"] / stats["total_executions"] * 100, 2
                    ),
                    "avg_time_ms": round(
                        stats["total_time_ms"] / stats["total_executions"], 2
                    ),
                    "timeout_count": stats["timeout_count"],
                    "last_executed": stats["last_executed"]
                }
        return result


# ============= 健康检查详细信息 =============

class HealthChecker:
    """健康检查器"""
    
    @staticmethod
    async def check_database() -> Dict[str, Any]:
        """检查数据库健康状态"""
        from app.database import check_db_connection
        return await check_db_connection()
    
    @staticmethod
    async def check_redis() -> Dict[str, Any]:
        """检查 Redis 健康状态"""
        if not cache._connected or not cache.client:
            return {"status": "unhealthy", "error": "Not connected"}
        
        try:
            start = time.time()
            await cache.client.ping()
            latency_ms = round((time.time() - start) * 1000, 2)
            
            info = await cache.client.info()
            
            return {
                "status": "healthy",
                "latency_ms": latency_ms,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    @staticmethod
    async def check_disk_space() -> Dict[str, Any]:
        """检查磁盘空间"""
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            return {
                "status": "healthy" if free > 1024 * 1024 * 1024 else "warning",  # 1GB 警告阈值
                "total_gb": round(total / (1024 * 1024 * 1024), 2),
                "used_gb": round(used / (1024 * 1024 * 1024), 2),
                "free_gb": round(free / (1024 * 1024 * 1024), 2),
                "percent_used": round(used / total * 100, 2)
            }
        except Exception as e:
            return {"status": "unknown", "error": str(e)}
    
    @classmethod
    async def get_full_health(cls) -> Dict[str, Any]:
        """获取完整健康检查报告"""
        checks = {
            "database": await cls.check_database(),
            "redis": await cls.check_redis(),
            "disk": await cls.check_disk_space()
        }
        
        # 判断整体状态
        all_healthy = all(
            check.get("status") == "healthy"
            for check in checks.values()
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks,
            "version": "1.0.0"
        }
