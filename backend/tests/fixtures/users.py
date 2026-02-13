"""
测试用户数据

提供各种测试场景的用户数据
"""

# 测试用户数据
TEST_USERS = [
    {
        "email": "user@example.com",
        "username": "testuser",
        "password": "password123",
        "role": "user"
    },
    {
        "email": "developer@example.com",
        "username": "devuser",
        "password": "password123",
        "role": "developer"
    },
    {
        "email": "admin@example.com",
        "username": "adminuser",
        "password": "password123",
        "role": "admin"
    }
]

# 测试会话数据
TEST_SESSIONS = [
    {
        "session_id": "test-session-1",
        "user_id": 1,
        "title": "Test Session 1",
        "status": "active"
    },
    {
        "session_id": "test-session-2",
        "user_id": 2,
        "title": "Test Session 2",
        "status": "completed"
    }
]

# 测试应用数据
TEST_APPS = [
    {
        "name": "Test App 1",
        "description": "A test application",
        "version": "1.0.0",
        "user_id": 1
    },
    {
        "name": "Test App 2",
        "description": "Another test application",
        "version": "2.0.0",
        "user_id": 2
    }
]
