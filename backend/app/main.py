"""
FastAPI主应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db, close_db
from app.core.rate_limit import rate_limit_middleware

# 创建FastAPI应用
app = FastAPI(
    title="OpenCode Platform API",
    description="OpenCode Web平台API",
    version="1.0.0"
)

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
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    await close_db()


@app.get("/")
async def root():
    """根路径"""
    return {"message": "OpenCode Platform API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

# 引入API路由
from app.api import api_router

app.include_router(api_router, prefix="/api")
