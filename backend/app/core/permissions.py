"""
权限检查模块

提供基于角色的权限控制
"""
from typing import List
from fastapi import HTTPException, status, Depends

from app.models.user import User
from app.dependencies import get_current_user


class PermissionChecker:
    """
    权限检查器
    
    检查用户是否具有所需权限
    """
    def __init__(self, required_permissions: List[str]):
        """
        初始化权限检查器
        
        Args:
            required_permissions: 所需权限列表
        """
        self.required_permissions = required_permissions
    
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """
        检查权限
        
        Args:
            current_user: 当前用户
            
        Returns:
            User: 当前用户
            
        Raises:
            HTTPException: 权限不足
        """
        # 检查用户是否是管理员
        if current_user.is_superuser:
            return current_user
        
        # 检查用户是否有所需权限
        user_permissions = set(current_user.permissions or [])
        required = set(self.required_permissions)
        
        if not required.issubset(user_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足。需要: {', '.join(self.required_permissions)}"
            )
        
        return current_user


def is_superuser(current_user: User = Depends(get_current_user)) -> User:
    """
    检查是否是超级管理员
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 当前用户
        
    Raises:
        HTTPException: 不是超级管理员
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    return current_user


def is_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    检查用户是否激活
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 当前用户
        
    Raises:
        HTTPException: 用户未激活
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户未激活"
        )
    return current_user


# 权限常量
class Permissions:
    """权限常量"""
    # 用户管理
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # 会话管理
    SESSION_READ = "session:read"
    SESSION_WRITE = "session:write"
    SESSION_DELETE = "session:delete"
    
    # 技能管理
    SKILL_READ = "skill:read"
    SKILL_WRITE = "skill:write"
    SKILL_DELETE = "skill:delete"
    
    # 应用管理
    APP_READ = "app:read"
    APP_WRITE = "app:write"
    APP_DELETE = "app:delete"
    
    # 系统管理
    SYSTEM_ADMIN = "system:admin"
