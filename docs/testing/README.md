# 测试环境说明

本文档说明OpenCode平台的测试环境配置和运行方法。

## 测试框架

OpenCode平台使用以下测试框架：

- **后端测试**: pytest + pytest-asyncio（异步测试支持）
- **前端测试**: Vitest（Phase 1，待实现）

## 测试结构

```
backend/
├── tests/
│   ├── conftest.py              # 测试配置和fixtures
│   ├── test_api/                # API测试
│   │   ├── test_auth.py        # 认证API测试
│   │   └── ...
│   ├── test_models/             # 模型测试（待实现）
│   ├── test_services/           # 服务层测试（待实现）
│   ├── fixtures/                # 测试数据
│   │   ├── users.py            # 测试用户数据
│   │   └── ...
│   └── test_opencode_sidecar.py # Sidecar测试
├── pytest.ini                   # pytest配置
└── requirements-test.txt        # 测试依赖
```

## 运行测试

### 后端测试

在backend目录下运行：

```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_api/test_auth.py

# 运行特定测试函数
pytest tests/test_api/test_auth.py::test_register

# 显示详细输出
pytest -v

# 显示打印输出
pytest -s
```

### 测试覆盖率

生成测试覆盖率报告：

```bash
cd backend

# 运行测试并生成覆盖率报告
pytest --cov=app tests/

# 生成HTML报告
pytest --cov=app --cov-report=html tests/

# 查看报告
open htmlcov/index.html
```

## 测试数据库

### 开发环境
- 数据库：PostgreSQL
- URL：通过环境变量 `DATABASE_URL` 配置

### 测试环境
- 数据库：SQLite（内存数据库）
- URL：`sqlite+aiosqlite:///./test.db`
- 优势：无需额外配置，测试速度快，易于清理

### 数据库隔离
- 每个测试函数都会创建新的数据库
- 测试结束后自动删除所有表
- 确保测试之间完全独立

## Mock策略

为了提高测试效率和稳定性，采用以下Mock策略：

### 外部服务Mock
- **LLM API调用**: 使用Mock模拟响应
- **opencode CLI调用**: 使用unittest.mock模拟subprocess
- **外部HTTP请求**: 使用httpx的Mock传输

### 数据库Mock
- 不Mock数据库，使用SQLite测试数据库
- 确保SQL查询逻辑正确
- 使用fixtures提供测试数据

### 示例：Mock OpenCode CLI

```python
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_opencode_sidecar_mock():
    sidecar = OpenCodeSidecar()
    
    with patch('asyncio.create_subprocess_exec') as mock_exec:
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"Success", b""))
        mock_exec.return_value = mock_proc
        
        result = await sidecar.execute("Hello", "test-session", "test-user")
        assert result['success'] is True
```

## 测试最佳实践

### 1. 测试独立性
- 每个测试应该独立运行
- 不依赖其他测试的结果
- 不依赖执行顺序

### 2. 使用Fixtures
```python
# conftest.py中的fixture
@pytest.fixture
async def test_user(db_session):
    user = User(email="test@example.com", username="testuser")
    db_session.add(user)
    await db_session.commit()
    return user

# 在测试中使用
@pytest.mark.asyncio
async def test_example(client, test_user):
    # test_user已经创建好
    pass
```

### 3. 清晰的测试命名
```python
# 好的命名
async def test_register_with_valid_data_should_succeed():
    pass

async def test_login_with_invalid_password_should_fail():
    pass
```

### 4. 测试覆盖边界情况
```python
@pytest.mark.asyncio
async def test_register_with_duplicate_email():
    """测试重复邮箱注册"""
    # 第一次注册
    await client.post("/api/auth/register", json=user_data)
    
    # 第二次注册（应该失败）
    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 400
```

## CI/CD集成

测试已集成到GitHub Actions中：

- 触发条件：push和pull request
- 自动运行所有测试
- 生成覆盖率报告
- PostgreSQL服务容器支持

详见：`.github/workflows/test.yml`

## 常见问题

### Q: 测试数据库冲突怎么办？
A: 测试数据库使用SQLite，每个测试函数独立创建和销毁，不会冲突。

### Q: 如何调试失败的测试？
A: 使用 `pytest -s --pdb` 进入调试模式，或添加 `print()` 语句并使用 `pytest -s`。

### Q: 如何只运行特定的测试？
A: 使用 `-k` 参数：
```bash
pytest -k "auth"  # 运行所有包含auth的测试
pytest -k "test_login"  # 运行test_login测试
```

### Q: 如何查看测试覆盖率详细报告？
A: 生成HTML报告：
```bash
pytest --cov=app --cov-report=html tests/
open htmlcov/index.html
```

## 扩展阅读

- [pytest文档](https://docs.pytest.org/)
- [pytest-asyncio文档](https://pytest-asyncio.readthedocs.io/)
- [FastAPI测试文档](https://fastapi.tiangolo.com/tutorial/testing/)
