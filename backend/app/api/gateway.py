"""
API网关管理路由

提供路由配置和API密钥管理接口
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database import get_db
from app.dependencies import get_current_user, get_current_user_optional
from app.models.user import User
from app.models.gateway import GatewayRoute, ApiKey
from app.schemas.gateway import (
    GatewayRouteCreate, GatewayRouteUpdate, GatewayRouteResponse, GatewayRouteListResponse,
    ApiKeyCreate, ApiKeyResponse, ApiKeyCreateResponse, ApiKeyListResponse,
    RateLimitStatus, GatewayStats, GatewayServiceStatus,
    AuthValidationResponse, ApiKeyAuth
)
from app.services.gateway_service import GatewayService, get_gateway_service
from app.core.exceptions import NotFoundException, ForbiddenException, ValidationException
from app.core.cache import cache

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 路由配置 API ====================

@router.post(
    "/routes",
    response_model=GatewayRouteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建路由",
    description="创建新的API网关路由配置"
)
async def create_route(
    route_data: GatewayRouteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建网关路由"""
    service = GatewayService(db, cache.client if cache._connected else None)
    
    try:
        route = await service.create_route(route_data, user_id=current_user.id)
        return GatewayRouteResponse.model_validate(route)
    except ValueError as e:
        raise ValidationException(str(e))


@router.get(
    "/routes",
    response_model=GatewayRouteListResponse,
    summary="获取路由列表",
    description="获取所有网关路由配置列表"
)
async def list_routes(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=500, description="返回的记录数"),
    is_active: Optional[bool] = Query(None, description="按激活状态过滤"),
    service_name: Optional[str] = Query(None, description="按服务名过滤"),
    tags: Optional[str] = Query(None, description="按标签过滤(逗号分隔)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """获取路由列表"""
    service = GatewayService(db, cache.client if cache._connected else None)
    
    tag_list = tags.split(",") if tags else None
    
    routes, total = await service.get_routes(
        skip=skip,
        limit=limit,
        is_active=is_active,
        service_name=service_name,
        tags=tag_list,
        user_id=current_user.id if current_user else None
    )
    
    return GatewayRouteListResponse(
        total=total,
        items=[GatewayRouteResponse.model_validate(r) for r in routes]
    )


@router.get(
    "/routes/{route_id}",
    response_model=GatewayRouteResponse,
    summary="获取路由详情",
    description="获取指定路由的详细配置"
)
async def get_route(
    route_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """获取单个路由详情"""
    service = GatewayService(db, cache.client if cache._connected else None)
    route = await service.get_route(route_id)
    
    if not route:
        raise NotFoundException(f"Route with id {route_id} not found")
    
    return GatewayRouteResponse.model_validate(route)


@router.put(
    "/routes/{route_id}",
    response_model=GatewayRouteResponse,
    summary="更新路由",
    description="更新指定路由的配置"
)
async def update_route(
    route_id: int,
    route_data: GatewayRouteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新路由配置"""
    service = GatewayService(db, cache.client if cache._connected else None)
    
    # 检查路由是否存在
    existing_route = await service.get_route(route_id)
    if not existing_route:
        raise NotFoundException(f"Route with id {route_id} not found")
    
    # 权限检查
    if existing_route.user_id and existing_route.user_id != current_user.id and not current_user.is_superuser:
        raise ForbiddenException("You don't have permission to update this route")
    
    try:
        route = await service.update_route(route_id, route_data)
        return GatewayRouteResponse.model_validate(route)
    except ValueError as e:
        raise ValidationException(str(e))


@router.delete(
    "/routes/{route_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除路由",
    description="删除指定的路由配置"
)
async def delete_route(
    route_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除路由"""
    service = GatewayService(db, cache.client if cache._connected else None)
    
    # 检查路由是否存在
    existing_route = await service.get_route(route_id)
    if not existing_route:
        raise NotFoundException(f"Route with id {route_id} not found")
    
    # 权限检查
    if existing_route.user_id and existing_route.user_id != current_user.id and not current_user.is_superuser:
        raise ForbiddenException("You don't have permission to delete this route")
    
    deleted = await service.delete_route(route_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete route"
        )


@router.post(
    "/routes/sync",
    summary="同步路由到网关",
    description="将所有活跃路由同步到Kong/Traefik网关"
)
async def sync_routes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """同步所有路由到外部网关"""
    if not current_user.is_superuser:
        raise ForbiddenException("Only administrators can sync routes")
    
    service = GatewayService(db, cache.client if cache._connected else None)
    result = await service.sync_all_routes()
    
    return {
        "message": "Route synchronization completed",
        "synced": result["synced"],
        "failed": result["failed"],
        "errors": result["errors"]
    }


# ==================== API密钥管理 API ====================

@router.post(
    "/keys",
    response_model=ApiKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="生成API密钥",
    description="生成新的API访问密钥"
)
async def create_api_key(
    key_data: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建API密钥"""
    service = GatewayService(db, cache.client if cache._connected else None)
    
    api_key, full_key = await service.create_api_key(key_data, current_user.id)
    
    response = ApiKeyCreateResponse.model_validate(api_key)
    response.key = full_key  # 只有创建时返回完整密钥
    
    return response


@router.get(
    "/keys",
    response_model=ApiKeyListResponse,
    summary="获取密钥列表",
    description="获取当前用户的所有API密钥"
)
async def list_api_keys(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=500, description="返回的记录数"),
    is_active: Optional[bool] = Query(None, description="按激活状态过滤"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取API密钥列表"""
    service = GatewayService(db, cache.client if cache._connected else None)
    
    keys, total = await service.get_api_keys(
        skip=skip,
        limit=limit,
        is_active=is_active,
        user_id=current_user.id
    )
    
    return ApiKeyListResponse(
        total=total,
        items=[ApiKeyResponse.model_validate(k) for k in keys]
    )


@router.get(
    "/keys/{key_id}",
    response_model=ApiKeyResponse,
    summary="获取密钥详情",
    description="获取指定API密钥的详细信息"
)
async def get_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个API密钥详情"""
    service = GatewayService(db, cache.client if cache._connected else None)
    api_key = await service.get_api_key(key_id)
    
    if not api_key:
        raise NotFoundException(f"API key with id {key_id} not found")
    
    # 权限检查
    if api_key.user_id != current_user.id and not current_user.is_superuser:
        raise ForbiddenException("You don't have permission to access this API key")
    
    return ApiKeyResponse.model_validate(api_key)


@router.delete(
    "/keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除密钥",
    description="删除指定的API密钥"
)
async def delete_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除API密钥"""
    service = GatewayService(db, cache.client if cache._connected else None)
    
    deleted = await service.delete_api_key(key_id, current_user.id)
    if not deleted:
        raise NotFoundException(f"API key with id {key_id} not found or not owned by you")


@router.post(
    "/keys/{key_id}/revoke",
    response_model=ApiKeyResponse,
    summary="撤销密钥",
    description="撤销（禁用）指定的API密钥"
)
async def revoke_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """撤销API密钥"""
    service = GatewayService(db, cache.client if cache._connected else None)
    
    revoked = await service.revoke_api_key(key_id, current_user.id)
    if not revoked:
        raise NotFoundException(f"API key with id {key_id} not found or not owned by you")
    
    api_key = await service.get_api_key(key_id)
    return ApiKeyResponse.model_validate(api_key)


# ==================== 认证验证 API ====================

@router.post(
    "/auth/validate",
    response_model=AuthValidationResponse,
    summary="验证认证",
    description="验证JWT令牌或API密钥的有效性"
)
async def validate_auth(
    request: Request,
    auth_data: Optional[ApiKeyAuth] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    验证认证
    
    支持:
    - Bearer Token (JWT)
    - X-API-Key Header
    - Request Body中的API密钥
    """
    service = GatewayService(db, cache.client if cache._connected else None)
    
    # 尝试从Header获取Authorization
    auth_header = request.headers.get("Authorization", "")
    api_key_header = request.headers.get("X-API-Key")
    
    # JWT认证
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        from app.core.security import decode_token
        
        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            user_id = payload.get("sub")
            return AuthValidationResponse(
                valid=True,
                auth_type="jwt",
                user_id=int(user_id) if user_id else None,
                scopes=["read", "write"],
                message="JWT token is valid"
            )
        
        return AuthValidationResponse(
            valid=False,
            auth_type="jwt",
            message="Invalid or expired JWT token"
        )
    
    # API Key认证
    api_key = api_key_header or (auth_data.api_key if auth_data else None)
    if api_key:
        key_info = await service.validate_api_key(api_key)
        
        if key_info and key_info.get("valid"):
            return AuthValidationResponse(
                valid=True,
                auth_type="api_key",
                user_id=key_info.get("user_id"),
                scopes=key_info.get("scopes", []),
                rate_limit=key_info.get("rate_limit"),
                message="API key is valid"
            )
        
        return AuthValidationResponse(
            valid=False,
            auth_type="api_key",
            message=key_info.get("reason", "Invalid API key") if key_info else "Invalid API key"
        )
    
    return AuthValidationResponse(
        valid=False,
        auth_type="none",
        message="No authentication provided"
    )


# ==================== 限流管理 API ====================

@router.get(
    "/ratelimit/{key:path}",
    response_model=RateLimitStatus,
    summary="获取限流状态",
    description="获取指定键的当前限流状态"
)
async def get_rate_limit_status(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取限流状态"""
    service = GatewayService(db, cache.client if cache._connected else None)
    
    status = await service.get_rate_limit_status(key)
    if not status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rate limit status not found"
        )
    
    return RateLimitStatus(
        key=key,
        limit=0,  # 需要从配置中获取
        remaining=status.get("current_count", 0),
        reset_at=status.get("reset_at", datetime.utcnow()),
        blocked=False
    )


@router.delete(
    "/ratelimit/{key:path}",
    summary="重置限流",
    description="重置指定键的限流计数"
)
async def reset_rate_limit(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重置限流计数"""
    if not current_user.is_superuser:
        raise ForbiddenException("Only administrators can reset rate limits")
    
    service = GatewayService(db, cache.client if cache._connected else None)
    reset = await service.reset_rate_limit(key)
    
    return {"message": "Rate limit reset successfully" if reset else "Failed to reset rate limit"}


# ==================== 网关状态 API ====================

@router.get(
    "/stats",
    response_model=GatewayStats,
    summary="获取网关统计",
    description="获取API网关的整体统计信息"
)
async def get_gateway_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取网关统计信息"""
    from sqlalchemy import func
    from datetime import date
    
    service = GatewayService(db, cache.client if cache._connected else None)
    
    # 获取路由统计
    total_routes = await db.scalar(
        func.count(GatewayRoute.id)
    ) or 0
    active_routes = await db.scalar(
        func.count(GatewayRoute.id).where(GatewayRoute.is_active == True)
    ) or 0
    
    # 获取API密钥统计
    total_keys = await db.scalar(
        func.count(ApiKey.id)
    ) or 0
    active_keys = await db.scalar(
        func.count(ApiKey.id).where(ApiKey.is_active == True)
    ) or 0
    
    # 获取今日请求统计（从限流日志）
    today = date.today()
    from app.models.gateway import RateLimitLog
    
    requests_today = await db.scalar(
        func.count(RateLimitLog.id).where(
            func.date(RateLimitLog.created_at) == today
        )
    ) or 0
    
    blocked_today = await db.scalar(
        func.count(RateLimitLog.id).where(
            func.date(RateLimitLog.created_at) == today,
            RateLimitLog.blocked == True
        )
    ) or 0
    
    # 服务状态（简化版本）
    services = [
        GatewayServiceStatus(
            name="Kong Gateway",
            status="connected" if hasattr(settings, 'KONG_ADMIN_URL') else "not_configured",
            routes_count=active_routes,
            healthy=True,
            last_check=datetime.utcnow()
        )
    ]
    
    return GatewayStats(
        total_routes=total_routes,
        active_routes=active_routes,
        total_api_keys=total_keys,
        active_api_keys=active_keys,
        requests_today=requests_today,
        blocked_requests_today=blocked_today,
        services=services
    )


@router.get(
    "/traefik/config",
    summary="获取Traefik配置",
    description="生成Traefik动态配置（用于文件或HTTP提供）"
)
async def get_traefik_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取Traefik动态配置"""
    if not current_user.is_superuser:
        raise ForbiddenException("Only administrators can access Traefik config")
    
    service = GatewayService(db, cache.client if cache._connected else None)
    config = await service.generate_traefik_config()
    
    return config


# ==================== 健康检查 ====================

@router.get(
    "/health",
    summary="网关健康检查",
    description="检查API网关服务的健康状态"
)
async def gateway_health_check():
    """网关健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "cache": "connected" if cache._connected else "disconnected"
    }
