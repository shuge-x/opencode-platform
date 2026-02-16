"""
数据库连接模块

提供SQLAlchemy异步引擎和会话管理
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# 命名约定（用于约束命名）
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """SQLAlchemy基类"""
    metadata = metadata


# 创建异步引擎（完整连接池配置）
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO or settings.DEBUG,
    future=True,
    # 连接池配置
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,  # 连接健康检查
    # 连接参数
    connect_args={
        "command_timeout": 60,
        "server_settings": {
            "jit": "off"  # 禁用JIT以避免首次查询延迟
        }
    }
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    依赖项：获取数据库会话
    
    Yields:
        AsyncSession: 数据库会话对象
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库（创建所有表）"""
    logger.info(f"Initializing database with pool_size={settings.DB_POOL_SIZE}, max_overflow={settings.DB_MAX_OVERFLOW}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """关闭数据库连接"""
    logger.info("Closing database connections...")
    await engine.dispose()


async def check_db_connection() -> dict:
    """
    检查数据库连接状态
    返回连接健康状态信息
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute("SELECT 1")
            result.fetchone()
            
            # 获取连接池状态
            pool = engine.pool
            return {
                "status": "healthy",
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalidatedcount() if hasattr(pool, 'invalidatedcount') else 0
            }
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
