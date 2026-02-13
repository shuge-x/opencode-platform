"""
API路由模块
"""
from fastapi import APIRouter

from app.api import auth, users, sessions, skills, apps

# 创建API路由器
api_router = APIRouter()

# 注册子路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["会话"])
api_router.include_router(skills.router, prefix="/skills", tags=["技能"])
api_router.include_router(apps.router, prefix="/apps", tags=["应用"])
