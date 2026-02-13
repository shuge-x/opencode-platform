# opencode Web管理平台

基于opencode的Web可视化管理平台，提供对话、技能开发、技能市场、应用化等功能。

## 技术栈

### 前端
- React 19 + TypeScript
- Zustand (状态管理)
- Ant Design (UI组件)
- Monaco Editor (代码编辑)
- WebSocket (实时通信)

### 后端
- Python 3.11+
- FastAPI (Web框架)
- Celery + Redis (任务队列)
- PostgreSQL (数据库)
- SQLAlchemy (ORM)

### 基础设施
- Docker + Docker Compose
- PostgreSQL 15
- Redis 7

## 核心模块

1. **Web Chat** - CLI功能的Web化
2. **Skills Dev** - 可视化技能开发环境
3. **Skills Hub** - 技能市场生态
4. **Skills App** - 技能应用化

## 快速开始

### 方式1：Docker Compose（推荐）

```bash
# 克隆项目
cd opencode-platform

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 访问
# 前端：http://localhost:3000
# 后端API：http://localhost:8000/docs
```

### 方式2：本地开发

#### 后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件

# 启动PostgreSQL和Redis（需要Docker）
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=opencode123 postgres:15
docker run -d -p 6379:6379 redis:7

# 初始化数据库
psql -U postgres -f ../docs/database/schema.sql
psql -U postgres -f ../docs/database/indexes.sql

# 启动后端
uvicorn app.main:app --reload

# 启动Celery Worker（新终端）
celery -A tasks.celery_app worker --loglevel=info
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问：
- 前端：http://localhost:3000
- API文档：http://localhost:8000/docs

## 项目结构

```
opencode-platform/
├── backend/              # Python后端
│   ├── app/             # FastAPI应用
│   │   ├── api/        # API路由
│   │   ├── models/     # 数据模型
│   │   ├── schemas/    # Pydantic模型
│   │   ├── core/       # 核心功能
│   │   └── utils/      # 工具函数
│   ├── tasks/           # Celery任务
│   ├── tests/           # 测试
│   └── requirements.txt # 依赖
├── frontend/             # React前端
│   ├── src/
│   │   ├── api/         # API客户端
│   │   ├── pages/       # 页面
│   │   ├── stores/      # 状态管理
│   │   ├── components/  # 组件
│   │   └── hooks/       # 自定义hooks
│   └── package.json     # 依赖
├── docs/                 # 文档
│   ├── database/        # 数据库设计
│   ├── api/             # API文档
│   └── PHASE*.md        # 阶段计划
├── docker-compose.yml    # Docker配置
└── README.md
```

## 开发阶段

- ✅ Phase 0: 架构准备（已完成）
- 🚀 Phase 1: Web Chat MVP（开发中）
- ⏳ Phase 2: Skills Dev（计划中）
- ⏳ Phase 3: Skills Hub（计划中）
- ⏳ Phase 4: Skills App（计划中）

## 文档

- [PRD](./docs/../openclaw-platform/PRD.md)
- [架构评审](./docs/../openclaw-platform/ARCHITECTURE_REVIEW.md)
- [并发架构分析](./docs/../openclaw-platform/CONCURRENCY_ANALYSIS.md)
- [数据库设计](./docs/database/)
- [API文档](http://localhost:8000/docs) - Swagger UI

## 团队

- 术维斯1号（研发主管）
- frontend-dev（前端工程师）
- backend-dev（后端工程师）
- qa-engineer（测试工程师）
- architect（架构师）

## License

MIT
