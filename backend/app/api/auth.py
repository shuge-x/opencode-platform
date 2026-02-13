"""
认证API路由

提供用户注册、登录和令牌管理功能
"""
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token, TokenRefresh
from app.core.security import (
    verify_password,
    get_password_hash,
    create_token_pair,
    decode_token,
    create_access_token
)
from app.config import settings

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    用户注册
    
    创建新用户账户并返回访问令牌
    
    Args:
        user_data: 用户注册数据
        db: 数据库会话
        
    Returns:
        dict: 包含访问令牌的响应
        
    Raises:
        HTTPException: 用户名或邮箱已存在
    """
    # 检查邮箱是否已存在
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 检查用户名是否已存在
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被使用"
        )
    
    # 创建用户
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 生成令牌
    token_pair = create_token_pair(user.id)
    token_pair["expires_in"] = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    return token_pair


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    用户登录
    
    验证用户凭据并返回访问令牌
    
    Args:
        credentials: 用户登录凭据
        db: 数据库会话
        
    Returns:
        dict: 包含访问令牌的响应
        
    Raises:
        HTTPException: 凭据无效
    """
    # 查找用户（支持用户名或邮箱登录）
    result = await db.execute(
        select(User).where(
            (User.username == credentials.username) |
            (User.email == credentials.username)
        )
    )
    user = result.scalar_one_or_none()
    
    # 验证用户和密码
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )
    
    # 生成令牌
    token_pair = create_token_pair(user.id)
    token_pair["expires_in"] = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    return token_pair


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    刷新令牌
    
    使用刷新令牌获取新的访问令牌
    
    Args:
        token_data: 刷新令牌数据
        db: 数据库会话
        
    Returns:
        dict: 包含新访问令牌的响应
        
    Raises:
        HTTPException: 刷新令牌无效
    """
    # 解码刷新令牌
    payload = decode_token(token_data.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 获取用户ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证用户是否存在且活跃
    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成新的令牌对
    token_pair = create_token_pair(user.id)
    token_pair["expires_in"] = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    return token_pair
