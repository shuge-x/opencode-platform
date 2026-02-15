"""
API网关服务

提供Kong/Traefik集成、路由管理、限流等功能
"""
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, or_
from sqlalchemy.orm import selectinload
import httpx
import logging
import redis.asyncio as aioredis

from app.config import settings
from app.models.gateway import GatewayRoute, ApiKey, RateLimitLog
from app.schemas.gateway import (
    GatewayRouteCreate, GatewayRouteUpdate,
    ApiKeyCreate, RateLimitConfig
)

logger = logging.getLogger(__name__)


class GatewayService:
    """API网关服务"""
    
    def __init__(self, db: AsyncSession, redis_client: Optional[aioredis.Redis] = None):
        self.db = db
        self.redis = redis_client
        self._http_client = None
    
    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client
    
    async def close(self):
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    # ==================== 路由管理 ====================
    
    async def create_route(
        self, 
        route_data: GatewayRouteCreate, 
        user_id: Optional[int] = None
    ) -> GatewayRoute:
        """创建路由"""
        # 检查名称是否已存在
        existing = await self.db.execute(
            select(GatewayRoute).where(GatewayRoute.name == route_data.name)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Route name '{route_data.name}' already exists")
        
        # 创建路由记录
        route = GatewayRoute(
            name=route_data.name,
            description=route_data.description,
            path=route_data.path,
            service_name=route_data.service_name,
            service_url=route_data.service_url,
            methods=route_data.methods,
            rate_limit=route_data.rate_limit,
            rate_limit_window=route_data.rate_limit_window,
            require_auth=route_data.require_auth,
            require_api_key=route_data.require_api_key,
            cors_enabled=route_data.cors_enabled,
            timeout_ms=route_data.timeout_ms,
            retry_count=route_data.retry_count,
            priority=route_data.priority,
            tags=route_data.tags or [],
            metadata=route_data.metadata or {},
            user_id=user_id,
            sync_status="pending"
        )
        
        self.db.add(route)
        await self.db.commit()
        await self.db.refresh(route)
        
        # 同步到外部网关
        try:
            await self._sync_route_to_gateway(route)
        except Exception as e:
            logger.warning(f"Failed to sync route to gateway: {e}")
        
        return route
    
    async def get_routes(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        service_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[int] = None
    ) -> Tuple[List[GatewayRoute], int]:
        """获取路由列表"""
        query = select(GatewayRoute)
        
        # 过滤条件
        if is_active is not None:
            query = query.where(GatewayRoute.is_active == is_active)
        if service_name:
            query = query.where(GatewayRoute.service_name == service_name)
        if user_id:
            query = query.where(GatewayRoute.user_id == user_id)
        if tags:
            # PostgreSQL JSON数组查询
            for tag in tags:
                query = query.where(GatewayRoute.tags.contains([tag]))
        
        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # 分页
        query = query.order_by(GatewayRoute.priority.desc(), GatewayRoute.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        routes = result.scalars().all()
        
        return list(routes), total
    
    async def get_route(self, route_id: int) -> Optional[GatewayRoute]:
        """获取单个路由"""
        result = await self.db.execute(
            select(GatewayRoute).where(GatewayRoute.id == route_id)
        )
        return result.scalar_one_or_none()
    
    async def get_route_by_name(self, name: str) -> Optional[GatewayRoute]:
        """根据名称获取路由"""
        result = await self.db.execute(
            select(GatewayRoute).where(GatewayRoute.name == name)
        )
        return result.scalar_one_or_none()
    
    async def update_route(
        self, 
        route_id: int, 
        route_data: GatewayRouteUpdate
    ) -> Optional[GatewayRoute]:
        """更新路由"""
        route = await self.get_route(route_id)
        if not route:
            return None
        
        # 更新字段
        update_data = route_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(route, field, value)
        
        route.sync_status = "pending"
        route.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(route)
        
        # 同步到外部网关
        try:
            await self._sync_route_to_gateway(route)
        except Exception as e:
            logger.warning(f"Failed to sync route to gateway: {e}")
        
        return route
    
    async def delete_route(self, route_id: int) -> bool:
        """删除路由"""
        route = await self.get_route(route_id)
        if not route:
            return False
        
        # 从外部网关删除
        try:
            await self._delete_route_from_gateway(route)
        except Exception as e:
            logger.warning(f"Failed to delete route from gateway: {e}")
        
        await self.db.delete(route)
        await self.db.commit()
        
        return True
    
    async def sync_all_routes(self) -> Dict[str, Any]:
        """同步所有路由到外部网关"""
        result = await self.db.execute(
            select(GatewayRoute).where(GatewayRoute.is_active == True)
        )
        routes = result.scalars().all()
        
        synced = 0
        failed = 0
        errors = []
        
        for route in routes:
            try:
                await self._sync_route_to_gateway(route)
                synced += 1
            except Exception as e:
                failed += 1
                errors.append({"route_id": route.id, "name": route.name, "error": str(e)})
        
        return {
            "synced": synced,
            "failed": failed,
            "errors": errors
        }
    
    # ==================== API密钥管理 ====================
    
    @staticmethod
    def _generate_api_key(prefix: str = "oc_live_") -> Tuple[str, str, str]:
        """
        生成API密钥
        
        Returns:
            (完整密钥, 哈希值, 前缀)
        """
        # 生成32字节的随机密钥
        key_bytes = secrets.token_bytes(32)
        key = prefix + key_bytes.hex()
        
        # 计算哈希
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        return key, key_hash, prefix
    
    async def create_api_key(
        self, 
        key_data: ApiKeyCreate, 
        user_id: int
    ) -> Tuple[ApiKey, str]:
        """
        创建API密钥
        
        Returns:
            (ApiKey对象, 完整密钥字符串)
        """
        # 生成密钥
        full_key, key_hash, key_prefix = self._generate_api_key()
        
        # 创建记录
        api_key = ApiKey(
            name=key_data.name,
            description=key_data.description,
            key_hash=key_hash,
            key_prefix=key_prefix,
            scopes=key_data.scopes,
            allowed_routes=key_data.allowed_routes or [],
            allowed_ips=key_data.allowed_ips or [],
            rate_limit=key_data.rate_limit,
            daily_limit=key_data.daily_limit,
            expires_at=key_data.expires_at,
            user_id=user_id
        )
        
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)
        
        return api_key, full_key
    
    async def get_api_keys(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        user_id: Optional[int] = None
    ) -> Tuple[List[ApiKey], int]:
        """获取API密钥列表"""
        query = select(ApiKey)
        
        if is_active is not None:
            query = query.where(ApiKey.is_active == is_active)
        if user_id:
            query = query.where(ApiKey.user_id == user_id)
        
        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # 分页
        query = query.order_by(ApiKey.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        keys = result.scalars().all()
        
        return list(keys), total
    
    async def get_api_key(self, key_id: int) -> Optional[ApiKey]:
        """获取单个API密钥"""
        result = await self.db.execute(
            select(ApiKey).where(ApiKey.id == key_id)
        )
        return result.scalar_one_or_none()
    
    async def delete_api_key(self, key_id: int, user_id: int) -> bool:
        """删除API密钥"""
        api_key = await self.get_api_key(key_id)
        if not api_key or api_key.user_id != user_id:
            return False
        
        await self.db.delete(api_key)
        await self.db.commit()
        
        return True
    
    async def revoke_api_key(self, key_id: int, user_id: int) -> bool:
        """撤销API密钥"""
        api_key = await self.get_api_key(key_id)
        if not api_key or api_key.user_id != user_id:
            return False
        
        api_key.is_active = False
        await self.db.commit()
        
        return True
    
    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        验证API密钥
        
        Returns:
            验证成功返回密钥信息，失败返回None
        """
        # 计算哈希
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # 查找密钥
        result = await self.db.execute(
            select(ApiKey).where(ApiKey.key_hash == key_hash)
        )
        key_record = result.scalar_one_or_none()
        
        if not key_record:
            return None
        
        # 检查状态
        if not key_record.is_active:
            return {"valid": False, "reason": "Key is inactive"}
        
        # 检查过期时间
        if key_record.expires_at and key_record.expires_at < datetime.utcnow():
            return {"valid": False, "reason": "Key has expired"}
        
        # 更新使用统计
        key_record.total_requests += 1
        key_record.last_used_at = datetime.utcnow()
        await self.db.commit()
        
        return {
            "valid": True,
            "key_id": key_record.id,
            "user_id": key_record.user_id,
            "scopes": key_record.scopes,
            "allowed_routes": key_record.allowed_routes,
            "rate_limit": key_record.rate_limit,
            "daily_limit": key_record.daily_limit
        }
    
    # ==================== 限流功能 ====================
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60
    ) -> Tuple[bool, int, int]:
        """
        检查限流
        
        Args:
            key: 限流键
            limit: 限制数量
            window_seconds: 时间窗口(秒)
            
        Returns:
            (是否允许, 剩余请求数, 重置时间戳)
        """
        if not self.redis:
            # 无Redis时，允许所有请求
            return True, limit, int(datetime.utcnow().timestamp()) + window_seconds
        
        redis_key = f"ratelimit:{key}"
        now = datetime.utcnow().timestamp()
        
        try:
            # 使用Redis滑动窗口
            pipe = self.redis.pipeline()
            
            # 移除过期的请求
            pipe.zremrangebyscore(redis_key, 0, now - window_seconds)
            # 添加当前请求
            pipe.zadd(redis_key, {str(now): now})
            # 获取当前计数
            pipe.zcard(redis_key)
            # 设置过期时间
            pipe.expire(redis_key, window_seconds)
            
            results = await pipe.execute()
            current_count = results[2]
            
            remaining = max(0, limit - current_count)
            reset_at = int(now + window_seconds)
            
            if current_count > limit:
                return False, 0, reset_at
            
            return True, remaining, reset_at
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True, limit, int(now + window_seconds)
    
    async def get_rate_limit_status(self, key: str) -> Optional[Dict[str, Any]]:
        """获取限流状态"""
        if not self.redis:
            return None
        
        redis_key = f"ratelimit:{key}"
        
        try:
            count = await self.redis.zcard(redis_key)
            ttl = await self.redis.ttl(redis_key)
            
            return {
                "key": key,
                "current_count": count,
                "ttl": ttl,
                "reset_at": datetime.utcnow() + timedelta(seconds=max(0, ttl))
            }
        except Exception as e:
            logger.error(f"Get rate limit status failed: {e}")
            return None
    
    async def reset_rate_limit(self, key: str) -> bool:
        """重置限流计数"""
        if not self.redis:
            return False
        
        redis_key = f"ratelimit:{key}"
        
        try:
            await self.redis.delete(redis_key)
            return True
        except Exception as e:
            logger.error(f"Reset rate limit failed: {e}")
            return False
    
    async def log_rate_limit_event(
        self,
        key_type: str,
        key_value: str,
        path: str,
        method: str,
        limit: int,
        window_seconds: int,
        current_count: int,
        blocked: bool,
        route_id: Optional[int] = None
    ) -> RateLimitLog:
        """记录限流事件"""
        log = RateLimitLog(
            key_type=key_type,
            key_value=key_value,
            route_id=route_id,
            path=path,
            method=method,
            limit=limit,
            window_seconds=window_seconds,
            current_count=current_count,
            blocked=blocked
        )
        
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        
        return log
    
    # ==================== Kong网关集成 ====================
    
    async def _sync_route_to_gateway(self, route: GatewayRoute) -> bool:
        """同步路由到Kong网关"""
        kong_admin_url = getattr(settings, 'KONG_ADMIN_URL', None)
        
        if not kong_admin_url:
            logger.info("Kong admin URL not configured, skipping sync")
            route.sync_status = "skipped"
            route.last_sync_at = datetime.utcnow()
            await self.db.commit()
            return True
        
        try:
            # 1. 创建或更新Service
            service_data = {
                "name": f"service-{route.name}",
                "url": route.service_url,
                "connect_timeout": route.timeout_ms,
                "write_timeout": route.timeout_ms,
                "read_timeout": route.timeout_ms,
                "retries": route.retry_count
            }
            
            if route.external_id:
                # 更新现有服务
                service_response = await self.http_client.patch(
                    f"{kong_admin_url}/services/{route.external_id}",
                    json=service_data
                )
            else:
                # 创建新服务
                service_response = await self.http_client.post(
                    f"{kong_admin_url}/services",
                    json=service_data
                )
            
            if service_response.status_code not in [200, 201]:
                raise Exception(f"Failed to create/update service: {service_response.text}")
            
            service = service_response.json()
            service_id = service["id"]
            
            # 2. 创建或更新Route
            route_data = {
                "name": f"route-{route.name}",
                "paths": [route.path],
                "methods": route.methods,
                "strip_path": False,
                "preserve_host": False,
                "protocols": ["http", "https"],
                "service": {"id": service_id}
            }
            
            # 查找现有路由
            routes_response = await self.http_client.get(
                f"{kong_admin_url}/routes",
                params={"name": f"route-{route.name}"}
            )
            
            if routes_response.status_code == 200:
                existing_routes = routes_response.json().get("data", [])
                if existing_routes:
                    # 更新现有路由
                    route_response = await self.http_client.patch(
                        f"{kong_admin_url}/routes/{existing_routes[0]['id']}",
                        json=route_data
                    )
                else:
                    # 创建新路由
                    route_response = await self.http_client.post(
                        f"{kong_admin_url}/routes",
                        json=route_data
                    )
            else:
                route_response = await self.http_client.post(
                    f"{kong_admin_url}/routes",
                    json=route_data
                )
            
            if route_response.status_code not in [200, 201]:
                raise Exception(f"Failed to create/update route: {route_response.text}")
            
            # 3. 添加插件
            await self._configure_kong_plugins(kong_admin_url, service_id, route)
            
            # 更新同步状态
            route.external_id = service_id
            route.sync_status = "synced"
            route.last_sync_at = datetime.utcnow()
            route.sync_error = None
            await self.db.commit()
            
            logger.info(f"Route {route.name} synced to Kong successfully")
            return True
            
        except Exception as e:
            route.sync_status = "failed"
            route.sync_error = str(e)
            route.last_sync_at = datetime.utcnow()
            await self.db.commit()
            
            logger.error(f"Failed to sync route {route.name} to Kong: {e}")
            return False
    
    async def _configure_kong_plugins(
        self, 
        kong_admin_url: str, 
        service_id: str, 
        route: GatewayRoute
    ):
        """配置Kong插件"""
        # Rate Limiting插件
        if route.rate_limit:
            plugin_data = {
                "name": "rate-limiting",
                "service": {"id": service_id},
                "config": {
                    "minute": route.rate_limit,
                    "policy": "redis" if self.redis else "local",
                    "redis_host": getattr(settings, 'REDIS_HOST', 'localhost'),
                    "redis_port": getattr(settings, 'REDIS_PORT', 6379),
                    "redis_password": getattr(settings, 'REDIS_PASSWORD', None)
                }
            }
            
            try:
                await self.http_client.post(
                    f"{kong_admin_url}/plugins",
                    json=plugin_data
                )
            except Exception as e:
                logger.warning(f"Failed to add rate-limiting plugin: {e}")
        
        # JWT认证插件
        if route.require_auth:
            plugin_data = {
                "name": "jwt",
                "service": {"id": service_id},
                "config": {
                    "claims_to_verify": ["exp"]
                }
            }
            
            try:
                await self.http_client.post(
                    f"{kong_admin_url}/plugins",
                    json=plugin_data
                )
            except Exception as e:
                logger.warning(f"Failed to add JWT plugin: {e}")
        
        # Key Auth插件
        if route.require_api_key:
            plugin_data = {
                "name": "key-auth",
                "service": {"id": service_id}
            }
            
            try:
                await self.http_client.post(
                    f"{kong_admin_url}/plugins",
                    json=plugin_data
                )
            except Exception as e:
                logger.warning(f"Failed to add key-auth plugin: {e}")
        
        # CORS插件
        if route.cors_enabled:
            plugin_data = {
                "name": "cors",
                "service": {"id": service_id},
                "config": {
                    "origins": ["*"],
                    "methods": route.methods,
                    "headers": ["Accept", "Accept-Version", "Content-Length", "Content-Type", "Date", "Authorization", "X-API-Key"],
                    "exposed_headers": ["X-Auth-Token"],
                    "credentials": True,
                    "max_age": 3600
                }
            }
            
            try:
                await self.http_client.post(
                    f"{kong_admin_url}/plugins",
                    json=plugin_data
                )
            except Exception as e:
                logger.warning(f"Failed to add CORS plugin: {e}")
    
    async def _delete_route_from_gateway(self, route: GatewayRoute) -> bool:
        """从Kong网关删除路由"""
        kong_admin_url = getattr(settings, 'KONG_ADMIN_URL', None)
        
        if not kong_admin_url or not route.external_id:
            return True
        
        try:
            # 删除服务（会级联删除路由和插件）
            await self.http_client.delete(
                f"{kong_admin_url}/services/{route.external_id}"
            )
            
            logger.info(f"Route {route.name} deleted from Kong")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete route from Kong: {e}")
            return False
    
    # ==================== Traefik集成 ====================
    
    async def generate_traefik_config(self) -> Dict[str, Any]:
        """生成Traefik动态配置"""
        result = await self.db.execute(
            select(GatewayRoute).where(GatewayRoute.is_active == True)
        )
        routes = result.scalars().all()
        
        http_config = {
            "routers": {},
            "services": {},
            "middlewares": {}
        }
        
        for route in routes:
            router_name = f"router-{route.name}"
            service_name = f"service-{route.name}"
            middleware_name = f"middleware-{route.name}"
            
            # 路由配置
            http_config["routers"][router_name] = {
                "rule": f"PathPrefix(`{route.path}`)",
                "service": service_name,
                "priority": route.priority,
                "middlewares": [middleware_name] if route.rate_limit or route.require_auth else [],
                "entryPoints": ["web", "websecure"]
            }
            
            # 服务配置
            http_config["services"][service_name] = {
                "loadBalancer": {
                    "servers": [{"url": route.service_url}],
                    "healthCheck": {
                        "interval": "30s",
                        "timeout": "5s"
                    }
                }
            }
            
            # 中间件配置
            middlewares = {}
            
            if route.rate_limit:
                middlewares["rateLimit"] = {
                    "average": route.rate_limit,
                    "burst": route.rate_limit * 2,
                    "period": f"{route.rate_limit_window}s"
                }
            
            if route.require_auth:
                middlewares["forwardAuth"] = {
                    "address": f"http://localhost:8000/api/gateway/auth/validate",
                    "authResponseHeaders": ["X-User-Id", "X-Scopes"]
                }
            
            if middlewares:
                http_config["middlewares"][middleware_name] = middlewares
        
        return {"http": http_config}


# 服务工厂函数
def get_gateway_service(db: AsyncSession) -> GatewayService:
    """获取网关服务实例"""
    from app.core.cache import cache
    return GatewayService(db, cache.client if cache._connected else None)
