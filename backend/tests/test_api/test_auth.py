"""
认证API测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    """测试用户注册"""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123"
        }
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    """测试用户登录"""
    # 先注册
    await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123"
        }
    )
    
    # 再登录
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
