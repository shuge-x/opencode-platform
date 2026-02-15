# Sprint 9: 技能版本管理 API

## 概述

本文档描述了技能版本管理后端 API 的实现，支持 Git 版本控制功能。

## 技术实现

### 核心组件

1. **GitService** (`app/services/git_service.py`)
   - 封装 GitPython 操作
   - 异步接口支持
   - 每个技能独立仓库

2. **SkillVersion Model** (`app/models/skill_version.py`)
   - 版本元数据存储
   - 与 Skill 关联

3. **API Router** (`app/api/skills_version.py`)
   - RESTful API 端点
   - 权限验证

### 依赖

- `GitPython==3.1.41` - Git 操作库

---

## API 端点

### 1. 仓库状态

#### GET `/api/skills/{skill_id}/repo/status`

获取技能 Git 仓库状态。

**响应示例:**
```json
{
  "initialized": true,
  "current_branch": "main",
  "current_commit": "abc1234567890",
  "is_dirty": false,
  "untracked_files": [],
  "modified_files": [],
  "staged_files": []
}
```

---

### 2. 仓库初始化

#### POST `/api/skills/{skill_id}/repo/init`

初始化技能的 Git 仓库。

**响应示例:**
```json
{
  "message": "Repository initialized successfully",
  "repo_path": "/tmp/skill_repos/skill_1",
  "files_added": 3
}
```

---

### 3. 版本列表

#### GET `/api/skills/{skill_id}/versions`

获取技能版本列表。

**查询参数:**
- `branch` (string, default: "main") - 分支名称
- `page` (int, default: 1) - 页码
- `page_size` (int, default: 20) - 每页数量

**响应示例:**
```json
{
  "items": [
    {
      "id": 1,
      "skill_id": 1,
      "user_id": 1,
      "version_name": "v1.0.0",
      "commit_hash": "abc1234567890abcdef1234567890abcdef1234",
      "short_hash": "abc1234",
      "commit_message": "Initial commit",
      "is_release": true,
      "is_latest": true,
      "files_changed": 3,
      "additions": 100,
      "deletions": 0,
      "created_at": "2024-02-15T10:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "has_more": false
}
```

---

### 4. 版本详情

#### GET `/api/skills/{skill_id}/versions/{version_id}`

获取指定版本的详细信息。

**路径参数:**
- `version_id` - commit hash（完整或短格式）

**响应示例:**
```json
{
  "id": 1,
  "skill_id": 1,
  "commit_hash": "abc1234567890abcdef1234567890abcdef1234",
  "short_hash": "abc1234",
  "message": "Initial commit",
  "author": {
    "name": "Developer",
    "email": "dev@example.com"
  },
  "timestamp": "2024-02-15T10:00:00",
  "parents": [],
  "file_changes": [
    {
      "file_path": "main.py",
      "change_type": "A",
      "old_file": null,
      "new_file": "main.py"
    }
  ],
  "is_release": true,
  "version_name": "v1.0.0"
}
```

---

### 5. 创建版本

#### POST `/api/skills/{skill_id}/versions`

创建新版本（提交变更）。

**请求体:**
```json
{
  "message": "Add new feature",
  "files": {
    "main.py": "print('hello world')"
  },
  "version_name": "v1.1.0",
  "is_release": false
}
```

**响应示例:**
```json
{
  "id": 2,
  "skill_id": 1,
  "user_id": 1,
  "version_name": "v1.1.0",
  "commit_hash": "def4567890abcdef1234567890abcdef123456",
  "short_hash": "def4567",
  "commit_message": "Add new feature",
  "is_release": false,
  "is_latest": true,
  "files_changed": 1,
  "additions": 1,
  "deletions": 0,
  "created_at": "2024-02-15T11:00:00"
}
```

---

### 6. 版本回退

#### POST `/api/skills/{skill_id}/versions/{version_id}/restore`

回退到指定版本。

**请求体:**
```json
{
  "create_backup": true
}
```

**响应示例:**
```json
{
  "success": true,
  "restored_to": "abc1234567890abcdef1234567890abcdef1234",
  "previous_commit": "def4567890abcdef1234567890abcdef123456",
  "message": "Restored to commit abc1234",
  "backup_branch": "backup-1708000000"
}
```

---

### 7. 版本对比

#### POST `/api/skills/{skill_id}/versions/compare`

对比两个版本。

**请求体:**
```json
{
  "from_commit": "abc1234",
  "to_commit": "def4567"
}
```

**响应示例:**
```json
{
  "from_commit": {
    "hash": "abc1234567890abcdef1234567890abcdef1234",
    "short_hash": "abc1234",
    "message": "Initial commit",
    "timestamp": "2024-02-15T10:00:00"
  },
  "to_commit": {
    "hash": "def4567890abcdef1234567890abcdef123456",
    "short_hash": "def4567",
    "message": "Add new feature",
    "timestamp": "2024-02-15T11:00:00"
  },
  "files_changed": 1,
  "diffs": [
    {
      "file_path": "main.py",
      "change_type": "M",
      "old_file": "main.py",
      "new_file": "main.py",
      "diff": "--- main.py\n+++ main.py\n@@ -1 +1,2 @@\n-print('hello')\n+print('hello world')"
    }
  ]
}
```

---

### 8. 分支管理

#### GET `/api/skills/{skill_id}/branches`

获取分支列表。

**响应示例:**
```json
[
  {
    "name": "main",
    "commit_hash": "abc1234567890abcdef1234567890abcdef1234",
    "is_current": true
  },
  {
    "name": "develop",
    "commit_hash": "def4567890abcdef1234567890abcdef123456",
    "is_current": false
  }
]
```

#### POST `/api/skills/{skill_id}/branches`

创建新分支。

**请求体:**
```json
{
  "branch_name": "feature-1",
  "from_commit": "abc1234"
}
```

#### POST `/api/skills/{skill_id}/branches/switch`

切换分支。

**请求体:**
```json
{
  "branch_name": "develop"
}
```

---

### 9. 获取指定版本文件

#### GET `/api/skills/{skill_id}/versions/{version_id}/files/{file_path}`

获取指定版本的文件内容。

**响应示例:**
```json
{
  "file_path": "main.py",
  "version_id": "abc1234",
  "content": "print('hello world')"
}
```

---

## 数据库模型

### SkillVersion

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| skill_id | Integer | 关联技能 |
| user_id | Integer | 创建用户 |
| version_name | String(100) | 版本名称（如 v1.0.0） |
| commit_hash | String(40) | Git commit hash |
| commit_message | Text | 提交信息 |
| is_release | Boolean | 是否正式发布 |
| is_latest | Boolean | 是否最新版本 |
| files_changed | Integer | 变更文件数 |
| additions | Integer | 新增行数 |
| deletions | Integer | 删除行数 |
| metadata | JSON | 额外元数据 |
| created_at | DateTime | 创建时间 |

---

## 并发安全

1. **线程池执行** - 所有 Git 操作在线程池中执行，避免阻塞事件循环
2. **独立仓库** - 每个技能使用独立的 Git 仓库路径
3. **异步接口** - 所有操作提供异步接口

---

## 文件结构

```
backend/
├── app/
│   ├── api/
│   │   └── skills_version.py    # 版本管理 API
│   ├── models/
│   │   └── skill_version.py     # 版本数据模型
│   ├── schemas/
│   │   └── skill_version.py     # 版本 Pydantic 模型
│   └── services/
│       ├── __init__.py
│       └── git_service.py       # Git 操作服务
├── alembic/versions/
│   └── 002_skill_versions.py    # 数据库迁移
└── tests/
    ├── test_skills_version.py   # API 测试
    └── test_git_service.py      # Git 服务测试
```

---

## 使用示例

### Python 客户端

```python
import httpx

async def create_version(skill_id: int, message: str, files: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8000/api/skills/{skill_id}/versions",
            json={
                "message": message,
                "files": files,
                "is_release": True
            },
            headers={"Authorization": "Bearer <token>"}
        )
        return response.json()

# 使用
result = await create_version(
    skill_id=1,
    message="Update main.py",
    files={"main.py": "# new content"}
)
```

### curl 示例

```bash
# 获取版本列表
curl -X GET "http://localhost:8000/api/skills/1/versions" \
  -H "Authorization: Bearer <token>"

# 创建新版本
curl -X POST "http://localhost:8000/api/skills/1/versions" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Update", "files": {"main.py": "print(1)"}}'

# 对比版本
curl -X POST "http://localhost:8000/api/skills/1/versions/compare" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"from_commit": "abc1234", "to_commit": "def4567"}'
```
