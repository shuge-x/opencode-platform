"""
API路由模块
"""
from fastapi import APIRouter

from app.api import auth, users, sessions, skills, apps, files, tools, skill_executor
from app.api import skills_version, skills_hub, gateway, monitoring, stats, billing
from app.api import workflows, workflow_executions, workflow_templates

# 创建API路由器
api_router = APIRouter()

# 注册子路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["会话"])
api_router.include_router(skills.router, prefix="/skills", tags=["技能"])
api_router.include_router(skill_executor.router, prefix="/skills/execution", tags=["技能执行"])
api_router.include_router(skills_version.router, prefix="/skills", tags=["技能版本管理"])
api_router.include_router(skills_hub.router, prefix="/skills-hub", tags=["技能市场"])
api_router.include_router(apps.router, prefix="/apps", tags=["应用"])
api_router.include_router(files.router, prefix="/files", tags=["文件"])
api_router.include_router(tools.router, prefix="/tools", tags=["工具"])
api_router.include_router(gateway.router, prefix="/gateway", tags=["API网关"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["技能监控"])
api_router.include_router(stats.router, prefix="/stats", tags=["统计"])
api_router.include_router(billing.router, prefix="/billing", tags=["计费"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(workflow_executions.router, prefix="/workflow-executions", tags=["workflow-executions"])
api_router.include_router(workflow_templates.router, tags=["workflow-templates"])
