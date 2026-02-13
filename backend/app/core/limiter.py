"""
API限流模块

使用slowapi实现请求限流
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request

from app.config import settings


def get_client_ip(request: Request) -> str:
    """
    获取客户端IP地址
    
    优先从X-Forwarded-For头获取真实IP
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        str: 客户端IP地址
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return get_remote_address(request)


# 创建限流器实例
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"]
)


def setup_limiter(app: FastAPI) -> None:
    """
    配置限流器
    
    Args:
        app: FastAPI应用实例
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
