"""
用户相关的Pydantic schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr = Field(..., description="用户邮箱")
    username: str = Field(..., min_length=3, max_length=100, description="用户名")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")


class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="密码（8-100位）"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "securepassword123",
                "full_name": "John Doe"
            }
        }
    )


class UserUpdate(BaseModel):
    """用户更新模型"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = None
    settings: Optional[dict] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "John Doe",
                "bio": "Software Developer"
            }
        }
    )


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    permissions: Optional[List[str]] = []
    roles: Optional[List[str]] = []
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe",
                "password": "securepassword123"
            }
        }
    )


class Token(BaseModel):
    """令牌响应模型"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }
    )


class TokenRefresh(BaseModel):
    """令牌刷新模型"""
    refresh_token: str = Field(..., description="刷新令牌")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    )
