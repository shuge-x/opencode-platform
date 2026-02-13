# Phase 0 开发计划

**阶段**: 架构准备
**时间**: 1-2周
**开始时间**: 2026-02-13
**负责人**: 术维斯1号（研发主管）

---

## 目标

搭建开发环境，完成技术预研，为Phase 1开发做准备。

---

## 核心任务

### 1. 项目基础设施（术维斯1号）

- [x] Git仓库初始化
- [ ] GitHub远程仓库创建
- [ ] CI/CD配置（GitHub Actions）
- [ ] 开发环境文档

### 2. 后端脚手架（backend-dev）

- [ ] FastAPI项目结构
- [ ] 数据库模型（SQLAlchemy）
- [ ] Redis连接
- [ ] Celery配置
- [ ] JWT认证
- [ ] API路由结构
- [ ] opencode Sidecar集成验证

**交付物**：
- `backend/` 完整的FastAPI脚手架
- 数据库迁移脚本
- 基础CRUD接口

### 3. 前端脚手架（frontend-dev）

- [ ] React + TypeScript项目
- [ ] Zustand状态管理
- [ ] Ant Design配置
- [ ] 路由配置
- [ ] API客户端封装
- [ ] WebSocket连接

**交付物**：
- `frontend/` 完整的React脚手架
- 基础页面结构
- API调用封装

### 4. 数据库设计（architect）

- [ ] ER图设计
- [ ] DDL脚本（PostgreSQL）
- [ ] 索引设计
- [ ] 数据库文档

**交付物**：
- `docs/database/` 数据库设计文档
- `backend/migrations/` 迁移脚本

### 5. API接口文档（architect）

- [ ] OpenAPI规范
- [ ] 接口定义
- [ ] 请求/响应示例
- [ ] API文档

**交付物**：
- `docs/api/` API接口文档
- Swagger UI配置

### 6. 测试环境（qa-engineer）

- [ ] 测试框架配置（pytest + pytest-asyncio）
- [ ] 测试数据库
- [ ] Mock数据准备
- [ ] CI测试配置

**交付物**：
- `backend/tests/` 测试脚手架
- 测试环境文档

---

## 技术预研

### 1. opencode Sidecar集成验证

**目标**：验证subprocess调用opencode CLI的可行性

**测试用例**：
```python
# backend/tests/test_opencode_sidecar.py
import asyncio
import subprocess

async def test_opencode_cli():
    """测试opencode CLI调用"""
    proc = await asyncio.create_subprocess_exec(
        'opencode', '--version',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    print(stdout.decode())
    assert proc.returncode == 0
```

### 2. Celery + Redis测试

**目标**：验证Celery任务队列配置

**测试用例**：
```python
# backend/tests/test_celery.py
from tasks import add

def test_celery_task():
    """测试Celery任务"""
    result = add.delay(2, 3)
    assert result.get(timeout=10) == 5
```

### 3. WebSocket连接测试

**目标**：验证FastAPI WebSocket

**测试用例**：
```python
# backend/tests/test_websocket.py
from fastapi.testclient import TestClient

def test_websocket():
    """测试WebSocket连接"""
    client = TestClient(app)
    with client.websocket_connect("/ws/test") as websocket:
        websocket.send_text("Hello")
        data = websocket.receive_text()
        assert data == "Hello"
```

---

## 里程碑

### Week 1 (2026-02-13 ~ 2026-02-20)

- [ ] 完成项目初始化（术维斯1号）
- [ ] 后端脚手架搭建（backend-dev）
- [ ] 前端脚手架搭建（frontend-dev）
- [ ] 数据库设计完成（architect）

### Week 2 (2026-02-20 ~ 2026-02-27)

- [ ] opencode Sidecar集成验证（backend-dev）
- [ ] Celery配置完成（backend-dev）
- [ ] 测试环境准备（qa-engineer）
- [ ] API接口文档完成（architect）
- [ ] Phase 0验收

---

## 验收标准

Phase 0验收需要满足：

1. ✅ 后端可启动（FastAPI + PostgreSQL + Redis + Celery）
2. ✅ 前端可启动（React开发服务器）
3. ✅ 数据库表创建成功
4. ✅ opencode CLI调用成功
5. ✅ Celery任务执行成功
6. ✅ WebSocket连接成功
7. ✅ API文档可访问（Swagger UI）
8. ✅ 测试框架可运行

---

## 风险与缓解

### 风险1：opencode CLI调用失败

**缓解措施**：
- 提前安装opencode并测试
- 准备Mock方案（如果opencode不可用）

### 风险2：Celery配置复杂

**缓解措施**：
- 使用Docker Compose简化环境
- 参考官方最佳实践

### 风险3：PostgreSQL环境问题

**缓解措施**：
- 使用Docker容器
- 提供SQLite备选方案（开发环境）

---

## 下一步

Phase 0完成后，启动Phase 1：Web Chat MVP开发。

---

**创建时间**: 2026-02-13
**最后更新**: 2026-02-13
**负责人**: 术维斯1号
