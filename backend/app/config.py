"""
配置管理模块

使用pydantic-settings从环境变量加载配置
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用配置类
    
    从环境变量加载配置，支持.env文件
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # 应用基础配置
    APP_NAME: str = "OpenCode Web Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # API配置
    API_V1_PREFIX: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/opencode"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OpenCode CLI配置
    OPENCODE_CLI_PATH: str = "opencode"
    OPENCODE_TIMEOUT: int = 300  # 5分钟超时
    
    # CORS配置
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # API限流配置
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # WebSocket配置
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 1000


# 全局配置实例
settings = Settings()
