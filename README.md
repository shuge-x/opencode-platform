# opencode Web管理平台

基于opencode的Web可视化管理平台，提供对话、技能开发、技能市场、应用化等功能。

## 技术栈

### 前端
- React 18 + TypeScript
- Zustand (状态管理)
- Ant Design (UI组件)
- Monaco Editor (代码编辑)

### 后端
- Python 3.11+
- FastAPI (Web框架)
- Celery + Redis (任务队列)
- PostgreSQL (数据库)

### 底层
- opencode CLI (Sidecar模式)

## 项目结构

```
opencode-platform/
├── backend/          # Python后端
│   ├── app/         # FastAPI应用
│   ├── tasks/       # Celery任务
│   └── tests/       # 测试
├── frontend/         # React前端
│   ├── src/         # 源代码
│   └── public/      # 静态资源
├── docs/             # 文档
├── scripts/          # 脚本
└── README.md
```

## 核心模块

1. **Web Chat** - CLI功能的Web化
2. **Skills Dev** - 可视化技能开发环境
3. **Skills Hub** - 技能市场生态
4. **Skills App** - 技能应用化

## 开发阶段

- Phase 0: 架构准备 (1-2周)
- Phase 1: Web Chat MVP (4-6周)
- Phase 2: Skills Dev (3-4周)
- Phase 3: Skills Hub (3-4周)
- Phase 4: Skills App (4-5周)

## 快速开始

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

## 文档

- [PRD](../openclaw-platform/PRD.md)
- [架构评审](../openclaw-platform/ARCHITECTURE_REVIEW.md)
- [并发架构分析](../openclaw-platform/CONCURRENCY_ANALYSIS.md)
- [技术调整说明](../openclaw-platform/TECH_ADJUSTMENTS.md)

## 团队

- 术维斯1号（研发主管）
- frontend-dev（前端工程师）
- backend-dev（后端工程师）
- qa-engineer（测试工程师）
- architect（架构师）

## License

MIT
