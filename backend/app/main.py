"""
FastAPI主应用 - 优化版
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
import logging
import sys

from app.config import settings
from app.database import init_db, close_db
from app.core.rate_limit import rate_limit_middleware
from app.core.exceptions import register_exception_handlers
from app.core.cache import cache
from app.core.monitoring import HealthChecker, MonitoringStats, SystemMetrics

# 配置日志
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        # 可以添加文件处理器等其他handler
    ]
)

logger = logging.getLogger(__name__)


# 创建FastAPI应用
app = FastAPI(
    title="OpenCode Platform API",
    description="""
## OpenCode Web Platform API

OpenCode Platform 是一个强大的技能管理和执行平台。

### 主要功能
- 🔐 用户认证和授权
- 🎯 技能创建、管理和执行
- 📝 会话管理
- 📁 文件管理
- 🔧 工具集成
- 🚀 实时WebSocket通信

### 错误码说明
所有API错误都遵循统一的错误码格式：`ERR_XXXX`

- **1xxx**: 通用错误
- **2xxx**: 认证错误
- **3xxx**: 资源错误
- **4xxx**: 用户错误
- **5xxx**: 技能错误
- **6xxx**: 会话错误
- **7xxx**: 文件错误
- **8xxx**: 数据库错误
- **9xxx**: 外部服务错误

详细错误码说明请查看 [错误码文档](/docs/errors)。
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {
            "name": "auth",
            "description": "认证相关操作，包括登录、注册、令牌刷新等",
        },
        {
            "name": "users",
            "description": "用户管理操作",
        },
        {
            "name": "skills",
            "description": "技能的CRUD操作和版本管理",
        },
        {
            "name": "sessions",
            "description": "会话管理操作",
        },
        {
            "name": "files",
            "description": "文件上传、下载和管理",
        },
        {
            "name": "tools",
            "description": "工具集成接口",
        },
    ]
)

# 注册异常处理器
register_exception_handlers(app)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 限流中间件
app.middleware("http")(rate_limit_middleware)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("Starting OpenCode Platform API...")
    
    # 初始化数据库
    await init_db()
    logger.info("Database initialized")
    
    # 连接Redis缓存
    await cache.connect()
    if cache._connected:
        logger.info("Redis cache connected")
    else:
        logger.warning("Redis cache not available - running without cache")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("Shutting down OpenCode Platform API...")
    
    # 断开Redis连接
    await cache.disconnect()
    logger.info("Redis cache disconnected")
    
    # 关闭数据库连接
    await close_db()
    logger.info("Database connections closed")


@app.get("/", tags=["root"])
async def root():
    """根路径"""
    return {
        "message": "OpenCode Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """基础健康检查（快速响应）"""
    return {
        "status": "healthy",
        "cache": "connected" if cache._connected else "disconnected"
    }


@app.get("/health/detailed", tags=["health"])
async def health_check_detailed():
    """
    详细健康检查
    
    返回所有依赖服务的详细健康状态
    """
    return await HealthChecker.get_full_health()


@app.get("/health/live", tags=["health"])
async def liveness_probe():
    """Kubernetes 存活探针"""
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
async def readiness_probe():
    """Kubernetes 就绪探针"""
    # 检查关键依赖
    db_health = await HealthChecker.check_database()
    redis_health = await HealthChecker.check_redis()
    
    is_ready = (
        db_health.get("status") == "healthy"
        # Redis 可以降级运行
    )
    
    if is_ready:
        return {"status": "ready"}
    else:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "checks": {
                    "database": db_health.get("status"),
                    "redis": redis_health.get("status")
                }
            }
        )


@app.get("/metrics", tags=["monitoring"])
async def get_metrics():
    """
    获取监控指标
    
    返回性能统计、错误统计和系统指标
    """
    stats = await MonitoringStats.get_full_stats()
    system = await SystemMetrics.collect()
    
    return {
        "monitoring": stats,
        "system": system
    }


# 引入API路由
from app.api import api_router
from app.api import websocket as session_websocket
from app.api import debug_websocket

app.include_router(api_router, prefix="/api")
app.include_router(session_websocket.router)
app.include_router(debug_websocket.router)
