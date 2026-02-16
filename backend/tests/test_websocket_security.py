"""
WebSocket 会话验证安全测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.main import app
from app.models.user import User
from app.models.session import Session
from app.core.security import create_access_token, get_password_hash


@pytest.fixture
def test_client():
    """同步测试客户端"""
    return TestClient(app)


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """创建测试用户"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("password123"),
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_user2(db_session: AsyncSession):
    """创建第二个测试用户"""
    user = User(
        email="test2@example.com",
        username="testuser2",
        hashed_password=get_password_hash("password123"),
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_session(db_session: AsyncSession, test_user: User):
    """创建测试会话"""
    session = Session(
        user_id=test_user.id,
        title="Test Session",
        status="created"
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
async def test_session2(db_session: AsyncSession, test_user2: User):
    """创建第二个用户的测试会话"""
    session = Session(
        user_id=test_user2.id,
        title="Test Session 2",
        status="created"
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


def test_websocket_session_validation_own_session(
    test_client: TestClient,
    test_user: User,
    test_session: Session
):
    """
    测试用户访问自己的会话（应该成功）
    
    验证步骤：
    1. 创建用户和会话
    2. 生成有效 token
    3. 连接 WebSocket
    4. 验证连接成功
    """
    # 生成 token
    token = create_access_token(data={"sub": str(test_user.id)})
    
    # 连接 WebSocket
    with test_client.websocket_connect(
        f"/ws/session/{test_session.id}?token={token}"
    ) as websocket:
        # 发送 ping 测试连接
        websocket.send_json({"type": "ping"})
        
        # 应该收到 pong 响应
        response = websocket.receive_json()
        assert response["type"] == "pong"


def test_websocket_session_validation_other_user_session(
    test_client: TestClient,
    test_user: User,
    test_user2: User,
    test_session2: Session
):
    """
    测试用户访问其他用户的会话（应该被拒绝）
    
    验证步骤：
    1. 创建两个用户和各自的会话
    2. 用户1 尝试访问用户2 的会话
    3. 验证连接被拒绝（4004）
    """
    # 生成用户1的 token
    token = create_access_token(data={"sub": str(test_user.id)})
    
    # 尝试连接用户2的会话
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with test_client.websocket_connect(
            f"/ws/session/{test_session2.id}?token={token}"
        ):
            pass
    
    # 验证关闭码为 4004（Session not found or access denied）
    assert exc_info.value.code == 4004


def test_websocket_session_validation_nonexistent_session(
    test_client: TestClient,
    test_user: User
):
    """
    测试访问不存在的会话
    
    验证步骤：
    1. 创建用户但不创建会话
    2. 尝试连接不存在的 session_id
    3. 验证连接被拒绝（4004）
    """
    # 生成 token
    token = create_access_token(data={"sub": str(test_user.id)})
    
    # 尝试连接不存在的会话（使用一个不存在的 ID）
    nonexistent_session_id = 99999
    
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with test_client.websocket_connect(
            f"/ws/session/{nonexistent_session_id}?token={token}"
        ):
            pass
    
    # 验证关闭码为 4004
    assert exc_info.value.code == 4004


def test_websocket_session_validation_invalid_token(
    test_client: TestClient,
    test_session: Session
):
    """
    测试无效 token
    
    验证步骤：
    1. 使用无效 token 连接
    2. 验证连接被拒绝（4001）
    """
    # 使用无效 token
    invalid_token = "invalid.token.here"
    
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with test_client.websocket_connect(
            f"/ws/session/{test_session.id}?token={invalid_token}"
        ):
            pass
    
    # 验证关闭码为 4001（Unauthorized）
    assert exc_info.value.code == 4001


def test_websocket_session_validation_no_token(
    test_client: TestClient,
    test_session: Session
):
    """
    测试缺少 token
    
    验证步骤：
    1. 不提供 token 连接
    2. 验证连接被拒绝
    """
    # 尝试不提供 token 连接
    with pytest.raises(Exception):  # 可能是 422 或其他错误
        with test_client.websocket_connect(
            f"/ws/session/{test_session.id}"
        ):
            pass


def test_websocket_session_validation_expired_token(
    test_client: TestClient,
    test_user: User,
    test_session: Session
):
    """
    测试过期的 token
    
    验证步骤：
    1. 创建过期的 token
    2. 尝试连接
    3. 验证连接被拒绝（4001）
    """
    from datetime import datetime, timedelta
    from jose import jwt
    from app.config import settings
    
    # 创建过期的 token（过期时间设置为1小时前）
    expired_time = datetime.utcnow() - timedelta(hours=1)
    token_data = {
        "sub": str(test_user.id),
        "exp": expired_time,
        "type": "access"
    }
    expired_token = jwt.encode(
        token_data,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with test_client.websocket_connect(
            f"/ws/session/{test_session.id}?token={expired_token}"
        ):
            pass
    
    # 验证关闭码为 4001（Unauthorized）
    assert exc_info.value.code == 4001


def test_websocket_session_validation_wrong_user_id_in_token(
    test_client: TestClient,
    test_session: Session
):
    """
    测试 token 中的用户 ID 与会话所有者不匹配
    
    验证步骤：
    1. 生成一个不存在的用户 ID 的 token
    2. 尝试连接会话
    3. 验证连接被拒绝（4004）
    """
    # 生成一个不存在的用户 ID 的 token
    fake_user_id = 99999
    token = create_access_token(data={"sub": str(fake_user_id)})
    
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with test_client.websocket_connect(
            f"/ws/session/{test_session.id}?token={token}"
        ):
            pass
    
    # 验证关闭码为 4004（Session not found or access denied）
    assert exc_info.value.code == 4004


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
