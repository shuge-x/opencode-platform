"""
工具调用 API 测试
"""
import pytest
from httpx import AsyncClient
from app.main import app
from app.models.tool import ToolCall, ToolStatus


@pytest.mark.asyncio
async def test_create_tool_call():
    """测试创建工具调用"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 先登录获取token
        login_response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]

        # 创建工具调用
        response = await client.post(
            "/api/tools",
            json={
                "session_id": 1,
                "tool_name": "test_tool",
                "tool_description": "Test tool",
                "parameters": {"arg1": "value1"},
                "requires_permission": False
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["tool_name"] == "test_tool"
        assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_tool_calls():
    """测试列出工具调用"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 先登录获取token
        login_response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]

        # 列出工具调用
        response = await client.get(
            "/api/tools",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_grant_permission():
    """测试权限确认"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 先登录获取token
        login_response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]

        # 创建需要权限的工具调用
        create_response = await client.post(
            "/api/tools",
            json={
                "session_id": 1,
                "tool_name": "dangerous_tool",
                "requires_permission": True,
                "permission_reason": "This tool can modify system files"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        tool_call_id = create_response.json()["id"]

        # 授权
        response = await client.post(
            f"/api/tools/{tool_call_id}/permission",
            json={
                "granted": True,
                "reason": "User approved"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["permission_granted"] is True
        assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_add_execution_log():
    """测试添加执行日志"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 先登录获取token
        login_response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]

        # 创建工具调用
        create_response = await client.post(
            "/api/tools",
            json={
                "session_id": 1,
                "tool_name": "test_tool"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        tool_call_id = create_response.json()["id"]

        # 添加日志
        response = await client.post(
            f"/api/tools/{tool_call_id}/logs",
            json={
                "tool_call_id": tool_call_id,
                "log_level": "INFO",
                "message": "Tool execution started"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["log_level"] == "INFO"
        assert "started" in data["message"]


@pytest.mark.asyncio
async def test_get_execution_logs():
    """测试获取执行日志"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 先登录获取token
        login_response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]

        # 创建工具调用并添加日志
        create_response = await client.post(
            "/api/tools",
            json={
                "session_id": 1,
                "tool_name": "test_tool"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        tool_call_id = create_response.json()["id"]

        # 添加多条日志
        for i in range(3):
            await client.post(
                f"/api/tools/{tool_call_id}/logs",
                json={
                    "tool_call_id": tool_call_id,
                    "log_level": "INFO",
                    "message": f"Log message {i}"
                },
                headers={"Authorization": f"Bearer {token}"}
            )

        # 获取日志
        response = await client.get(
            f"/api/tools/{tool_call_id}/logs",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
