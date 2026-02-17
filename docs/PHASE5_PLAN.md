# Phase 5: 技能编排系统（Workflow Engine）

## 1. 概述

### 1.1 目标
构建可视化技能编排平台，让用户能够将多个技能组合成复杂工作流，实现自动化任务执行。

### 1.2 核心价值
- 解决单一技能能力有限的痛点
- 开启复杂自动化场景
- 提升平台竞争力（类似 Zapier/n8n）

### 1.3 工期估算

| 指标 | 值 |
|------|-----|
| 传统开发工期 | 12 天（2 周） |
| AI 开发工期 | ~13 小时（约 2 天） |
| **提效比** | **~6x** |

> 基于 Phase 1-4 历史数据：平均提效 10-15x

### 1.3 技术选型
- **前端可视化**：React Flow（节点编辑器） + Zustand（状态管理）
- **工作流引擎**：自研轻量级引擎（基于 DAG 执行）
- **任务调度**：Celery Beat（定时） + Redis（队列）
- **数据存储**：PostgreSQL（工作流定义） + Redis（执行状态）

---

## 2. 功能范围

### Phase 5.1: 工作流编辑器（Sprint 19-20）
- 可视化节点编辑器（拖拽式）
- 节点类型：技能节点、条件节点、数据变换节点
- 连接与数据流配置
- 工作流保存/加载

### Phase 5.2: 工作流引擎（Sprint 21-22）
- DAG 执行引擎
- 变量系统（输入/输出引用）
- 条件分支逻辑
- 错误处理与重试

### Phase 5.3: 触发与调度（Sprint 23-24）
- 手动触发
- 定时任务（Cron）
- Webhook 触发
- 执行历史与日志

---

## 3. Sprint 规划

> **工期说明**：
> - **传统工期**：按人工开发速度估算（1人全职）
> - **AI 开发工期**：按 AI 辅助开发速度估算（多智能体并行）
> - **提效比**：传统工期 / AI 开发工期

| Sprint | 传统工期 | AI 开发工期 | 提效比 |
|--------|----------|-------------|--------|
| Sprint 19 | 2 天 | 2 小时 | 8x |
| Sprint 20 | 2 天 | 2 小时 | 8x |
| Sprint 21 | 2 天 | 3 小时 | 5x |
| Sprint 22 | 2 天 | 2 小时 | 8x |
| Sprint 23 | 2 天 | 2 小时 | 8x |
| Sprint 24 | 2 天 | 2 小时 | 8x |
| **总计** | **12 天** | **~13 小时（约 2 天）** | **~6x** |

> **历史数据参考**：
> - Phase 1：传统 14 天 → AI 1 天（14x 提效）
> - Phase 2：传统 10 天 → AI 1 天（10x 提效）
> - Phase 3：传统 10 天 → AI 0.5 天（20x 提效）
> - Phase 4：传统 14 天 → AI 1 天（14x 提效）

---

### Sprint 19: 编辑器基础
**工期**：传统 2 天 / AI 2 小时

**目标**：搭建可视化编辑器框架

**任务**：
- [ ] 集成 React Flow
- [ ] 实现画布与节点拖拽
- [ ] 创建基础节点类型（Start/End/Skill）
- [ ] 节点属性面板

**交付**：
- 可拖拽的空白画布
- 3 种基础节点可添加
- 节点可连接

### Sprint 20: 编辑器完善
**工期**：传统 2 天 / AI 2 小时

**目标**：完整编辑器功能

**任务**：
- [ ] 条件节点（if/else）
- [ ] 数据变换节点
- [ ] 变量配置面板
- [ ] 工作流保存/加载 API
- [ ] 前端工作流列表页

**交付**：
- 完整节点类型
- 工作流 CRUD
- 数据流可视化

### Sprint 21: 执行引擎核心
**工期**：传统 2 天 / AI 3 小时（复杂度较高）

**目标**：工作流可执行

**任务**：
- [ ] DAG 解析与验证
- [ ] 顺序执行器
- [ ] 变量系统实现
- [ ] 条件分支执行
- [ ] 技能调用集成

**交付**：
- 手动触发执行
- 执行结果返回

### Sprint 22: 执行引擎增强
**工期**：传统 2 天 / AI 2 小时

**目标**：健壮的执行引擎

**任务**：
- [ ] 并行执行支持
- [ ] 错误处理分支
- [ ] 重试机制
- [ ] 执行日志记录
- [ ] 执行状态 API

**交付**：
- 稳定执行能力
- 错误自动处理

### Sprint 23: 触发系统
**工期**：传统 2 天 / AI 2 小时

**目标**：多种触发方式

**任务**：
- [ ] 定时任务调度（Celery Beat）
- [ ] Webhook 端点
- [ ] 触发器配置 UI
- [ ] 执行历史列表
- [ ] 执行详情页

**交付**：
- Cron 触发
- Webhook 触发
- 完整执行记录

### Sprint 24: 优化与文档
**工期**：传统 2 天 / AI 2 小时

**目标**：生产就绪

**任务**：
- [ ] 性能优化（大工作流）
- [ ] 模板工作流（预置示例）
- [ ] 用户文档
- [ ] API 文档
- [ ] 测试补充

**交付**：
- 生产级质量
- 完整文档

---

## 4. 数据模型

### 4.1 Workflow 表
```python
class Workflow(Base):
    id: UUID
    name: str
    description: str
    user_id: UUID  # owner
    definition: JSON  # 节点+连接定义
    variables: JSON  # 输入变量定义
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

### 4.2 WorkflowExecution 表
```python
class WorkflowExecution(Base):
    id: UUID
    workflow_id: UUID
    trigger_type: str  # manual/scheduled/webhook
    status: str  # pending/running/completed/failed
    input_data: JSON
    output_data: JSON
    started_at: datetime
    finished_at: datetime
    error_message: str
```

### 4.3 WorkflowExecutionStep 表
```python
class WorkflowExecutionStep(Base):
    id: UUID
    execution_id: UUID
    node_id: str
    node_type: str
    status: str
    input_data: JSON
    output_data: JSON
    started_at: datetime
    finished_at: datetime
    error_message: str
```

---

## 5. API 设计

### 5.1 工作流管理
```
GET    /api/v1/workflows           # 列表
POST   /api/v1/workflows           # 创建
GET    /api/v1/workflows/{id}      # 详情
PUT    /api/v1/workflows/{id}      # 更新
DELETE /api/v1/workflows/{id}      # 删除
```

### 5.2 执行管理
```
POST   /api/v1/workflows/{id}/execute       # 手动执行
GET    /api/v1/workflows/{id}/executions    # 执行历史
GET    /api/v1/executions/{id}              # 执行详情
POST   /api/v1/executions/{id}/cancel       # 取消执行
```

### 5.3 Webhook
```
POST   /api/v1/webhooks/{token}   # Webhook 触发
```

---

## 6. 前端架构

### 6.1 新增页面
- `/workflows` - 工作流列表
- `/workflows/new` - 创建工作流
- `/workflows/{id}/edit` - 编辑工作流
- `/workflows/{id}/executions` - 执行历史
- `/executions/{id}` - 执行详情

### 6.2 核心组件
- `WorkflowEditor` - 编辑器主组件
- `NodePalette` - 节点面板（拖拽源）
- `Canvas` - 画布（React Flow）
- `NodeConfigPanel` - 节点配置面板
- `VariablePanel` - 变量面板
- `ExecutionViewer` - 执行可视化

### 6.3 状态管理
```typescript
interface WorkflowState {
  currentWorkflow: Workflow | null;
  nodes: Node[];
  edges: Edge[];
  variables: Variable[];
  selectedNode: string | null;
  isExecuting: boolean;
}
```

---

## 7. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| React Flow 学习曲线 | 中 | 提前 POC，参考官方示例 |
| 并行执行复杂度 | 高 | 先实现顺序执行，渐进增强 |
| 循环依赖检测 | 中 | 实现拓扑排序验证 |
| 大工作流性能 | 中 | 虚拟化渲染，懒加载节点 |

---

## 8. 里程碑

| 阶段 | 传统工期 | AI 开发工期 | 提效比 |
|------|----------|-------------|--------|
| Sprint 19-20 完成 | 4 天 | 4 小时 | 8x |
| Sprint 21-22 完成 | 4 天 | 5 小时 | 6x |
| Sprint 23-24 完成 | 4 天 | 4 小时 | 8x |
| **Phase 5 总计** | **12 天** | **~13 小时（约 2 天）** | **~6x** |

**目标完成日期**：2026-02-18（AI 开发）/ 2026-03-01（传统开发）

---

## 9. 后续扩展（Phase 6+）

- AI 辅助编排（自然语言生成工作流）
- 工作流市场（分享/订阅）
- 子工作流（嵌套调用）
- 实时协作编辑
- 更多触发器（邮件、消息队列）
