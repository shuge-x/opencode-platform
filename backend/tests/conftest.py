"""
测试配置文件

提供pytest fixtures和测试环境配置
"""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
from app.main import app
from app.database import Base, get_db

# 测试数据库URL（SQLite）
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session():
    """创建测试数据库会话"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建会话工厂
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    # 清理：删除所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session):
    """创建测试客户端"""
    async def override_get_db():
        yield db_session
    
    # 覆盖数据库依赖
    app.dependency_overrides[get_db] = override_get_db
    
    # 创建异步客户端
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # 清理依赖覆盖
    app.dependency_overrides.clear()
