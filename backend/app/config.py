"""
配置管理模块

使用pydantic-settings从环境变量加载配置
"""
from typing import Optional, List
from pydantic import field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

logger = logging.getLogger(__name__)


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
    BASE_DIR: str = "/tmp"  # 基础目录，用于文件存储等
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # API配置
    API_V1_PREFIX: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/opencode"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    
    # JWT配置
    SECRET_KEY: str  # 必须从环境变量加载，无默认值
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """验证 SECRET_KEY 至少 32 字符"""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long for security")
        return v
    
    # OpenCode CLI配置
    OPENCODE_CLI_PATH: str = "opencode"
    OPENCODE_TIMEOUT: int = 300  # 5分钟超时
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # API限流配置
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # WebSocket配置
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 1000
    
    # MinIO配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str  # 必须从环境变量加载，无默认值
    MINIO_SECRET_KEY: str  # 必须从环境变量加载，无默认值
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "skills-hub"
    
    @field_validator("MINIO_ACCESS_KEY")
    @classmethod
    def validate_minio_access_key(cls, v: str) -> str:
        """验证 MINIO_ACCESS_KEY 不为空且不使用默认值"""
        if not v or v == "minioadmin":
            raise ValueError("MINIO_ACCESS_KEY must be set and cannot use default value 'minioadmin'")
        return v
    
    @field_validator("MINIO_SECRET_KEY")
    @classmethod
    def validate_minio_secret_key(cls, v: str) -> str:
        """验证 MINIO_SECRET_KEY 不为空且不使用默认值"""
        if not v or v == "minioadmin":
            raise ValueError("MINIO_SECRET_KEY must be set and cannot use default value 'minioadmin'")
        return v
    
    # 技能包配置
    MAX_PACKAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # 技能执行资源限制
    SKILL_EXECUTION_TIMEOUT: int = 60  # 秒
    SKILL_MEMORY_LIMIT: str = "256m"
    SKILL_CPU_QUOTA: int = 50000  # 50% CPU
    SKILL_MAX_OUTPUT_SIZE: int = 1024 * 1024  # 1MB 输出限制
    
    # API网关配置 (Kong)
    KONG_ADMIN_URL: Optional[str] = None  # 例如: http://kong-admin:8001
    KONG_PROXY_URL: Optional[str] = None  # 例如: http://kong-proxy:8000
    
    # Traefik配置 (可选)
    TRAEFIK_API_URL: Optional[str] = None  # 例如: http://traefik:8080
    
    # 网关限流配置
    GATEWAY_DEFAULT_RATE_LIMIT: int = 60  # 默认每分钟请求数
    GATEWAY_RATE_LIMIT_WINDOW: int = 60  # 限流窗口(秒)
    
    def validate_production_config(self) -> List[str]:
        """
        验证生产环境配置安全性
        返回警告列表，空列表表示验证通过
        """
        warnings = []
        
        if self.ENVIRONMENT == "production":
            if self.DEBUG:
                warnings.append("DEBUG mode should be disabled in production")
            if "localhost" in self.DATABASE_URL:
                warnings.append("DATABASE_URL should not use localhost in production")
            if "localhost" in self.REDIS_URL:
                warnings.append("REDIS_URL should not use localhost in production")
            if "localhost" in self.MINIO_ENDPOINT:
                warnings.append("MINIO_ENDPOINT should not use localhost in production")
            if not self.MINIO_SECURE:
                warnings.append("MINIO_SECURE should be True in production")
            if len(self.CORS_ORIGINS) == 0:
                warnings.append("CORS_ORIGINS should be explicitly set in production")
            if "http://localhost" in str(self.CORS_ORIGINS):
                warnings.append("CORS_ORIGINS should not include localhost in production")
        
        return warnings


# 全局配置实例
settings = Settings()

# 启动时验证环境配置
_config_warnings = settings.validate_production_config()
if _config_warnings:
    for warning in _config_warnings:
        logger.warning(f"Configuration warning: {warning}")
