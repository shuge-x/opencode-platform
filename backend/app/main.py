"""
FastAPI主应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db, close_db

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

# TODO: 添加API路由
from app.api import auth, users, sessions, skills, apps, websocket, files

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(skills.router, prefix="/api/skills", tags=["skills"])
app.include_router(apps.router, prefix="/api/apps", tags=["apps"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(websocket.router, tags=["websocket"])
