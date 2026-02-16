# Bug 修复工作流程

**版本**: 1.0  
**创建日期**: 2026-02-16  
**最后更新**: 2026-02-16

---

## 📋 概述

本文档定义了 opencode-platform 项目的 Bug 修复工作流程，适用于 AI agent 团队协作。

---

## 🎯 核心原则

1. **谁发现谁创建**：发现 bug 的人负责创建 GitHub Issue
2. **谁创建谁验证**：创建 Issue 的人负责验证修复并关闭 Issue
3. **职责明确**：每个角色有清晰的职责边界
4. **快速迭代**：P0 缺陷当天修复，P1 缺陷 3 天内修复

---

## 📊 优先级定义

| 级别 | 名称 | 响应时间 | 修复时间 | 示例 |
|------|------|---------|---------|------|
| P0 | Critical | 立即 | 当天 | 安全漏洞、数据丢失 |
| P1 | High | 1 天内 | 3 天内 | 功能失效、性能问题 |
| P2 | Medium | 3 天内 | 1 周内 | 体验问题、小 bug |
| P3 | Low | 1 周内 | 下个版本 | 优化建议、文档问题 |

---

## 🔄 完整流程

### 阶段 1：Bug 发现与 Issue 创建

**负责人**: qa-engineer（或其他发现者）

**步骤**：
1. 测试或使用过程中发现 bug
2. 记录详细信息：
   - Bug 描述
   - 复现步骤
   - 预期结果 vs 实际结果
   - 环境信息
   - 截图/日志（如有）
3. 在 GitHub 创建 Issue
4. 添加标签（见下方标签系统）
5. 设置优先级（P0/P1/P2/P3）
6. 分配负责人

**Issue 模板**：
```markdown
## Bug 描述
[清晰简洁地描述问题]

## 复现步骤
1. 
2. 
3. 

## 预期结果
[应该发生什么]

## 实际结果
[实际发生了什么]

## 环境信息
- **版本**: v1.0.0
- **模块**: [Web Chat / Skills Dev / Skills Hub / Skills App]
- **浏览器**: [Chrome / Firefox / Safari]
- **操作系统**: [Windows / macOS / Linux]

## 严重级别
- [ ] P0 - Critical（严重）
- [ ] P1 - High（高）
- [ ] P2 - Medium（中）
- [ ] P3 - Low（低）

## 相关文件
- 文件路径：
- 行号：

## 截图/日志
[如有，请附上]

## 测试报告链接
[链接到详细测试报告]
```

---

### 阶段 2：Issue 分配与领取

**负责人**: 研发主管（dev-lead）或开发 agent

**分配规则**：
- 后端 bug → `backend-dev`
- 前端 bug → `frontend-dev`
- 架构问题 → `architect`
- 测试问题 → `qa-engineer`

**看板流程**：
```
Backlog → Todo → In Progress → In Review → Done
```

---

### 阶段 3：开发修复

**负责人**: 对应开发 agent（backend-dev / frontend-dev）

**步骤**：

#### 3.1 创建分支
```bash
# 分支命名规范：bugfix/BUG-XXX-简短描述
git checkout main
git pull origin main
git checkout -b bugfix/BUG-001-skill-model-inconsistency
```

#### 3.2 修复 bug
- 修改代码
- 编写/更新单元测试
- 本地测试验证

#### 3.3 提交代码
```bash
# Commit Message 规范
git add .
git commit -m "fix(skills): add missing fields to Skill model

- Add prompt_template field
- Add category field
- Add slug field
- Add use_count field

Closes #1"
```

**Commit 类型**：
- `fix`: 修复 bug
- `feat`: 新功能
- `test`: 添加测试
- `refactor`: 重构
- `docs`: 文档更新
- `style`: 代码格式
- `perf`: 性能优化
- `chore`: 构建/工具

#### 3.4 推送分支
```bash
git push origin bugfix/BUG-001-skill-model-inconsistency
```

---

### 阶段 4：提交 Pull Request

**负责人**: 开发 agent

**PR 标题格式**：
```
<type>(<scope>): <subject>
```

**示例**：
```
fix(skills): add missing fields to Skill model
```

**PR 描述模板**：
```markdown
## 关联 Issue
Closes #1

## 修复内容
- [x] 添加缺失的 Skill 模型字段
- [x] 更新 Schema 定义
- [x] 添加数据库迁移脚本
- [x] 编写单元测试

## 测试
- [x] 本地测试通过
- [x] 单元测试通过
- [ ] 集成测试通过

## 变更类型
- [ ] Bug fix（修复 bug）
- [ ] New feature（新功能）
- [ ] Breaking change（破坏性变更）
- [ ] Documentation update（文档更新）

## 截图（如有 UI 变更）
[截图]
```

---

### 阶段 5：代码审核

**负责人**: 研发主管（dev-lead）或架构师（architect）

**审核要点**：
- [ ] 代码质量
- [ ] 测试覆盖
- [ ] 符合规范
- [ ] 没有引入新问题
- [ ] 文档更新

**审核结果**：
- ✅ Approve：可以合并
- 💬 Comment：需要讨论
- ❌ Request Changes：需要修改

---

### 阶段 6：CI/CD 检查

**自动执行**：
- 单元测试
- 代码风格检查（ESLint / Black）
- 类型检查（TypeScript / mypy）
- 安全扫描

**通过标准**：
- 所有测试通过
- 代码覆盖率不降低
- 无严重安全漏洞

---

### 阶段 7：合并代码

**负责人**: 研发主管（dev-lead）

**合并方式**：
- 使用 "Squash and merge" 压缩提交
- 或 "Rebase and merge" 保持提交历史

**合并后操作**：
1. 删除分支
2. 通知 qa-engineer 验证

---

### 阶段 8：验证与关闭

**负责人**: qa-engineer（Issue 创建者）

**步骤**：
1. 拉取最新代码
2. 验证 bug 已修复
3. 更新测试报告
4. 在 Issue 中添加验证结果
5. 关闭 Issue

**验证通过示例**：
```markdown
## 验证结果
✅ 已验证修复

**验证步骤**：
1. 创建技能时包含 prompt_template 字段
2. 成功保存到数据库
3. API 返回正确响应

**环境**：
- 版本：commit abc123
- 时间：2026-02-16 10:00 UTC
```

**验证失败**：
- 重新打开 Issue
- 添加失败原因
- 重新分配给开发 agent

---

## 🏷️ GitHub 标签系统

### 优先级标签
- `P0-critical` - 🔴 严重
- `P1-high` - 🟠 高
- `P2-medium` - 🟡 中
- `P3-low` - 🟢 低

### 类型标签
- `bug` - 🐛 缺陷
- `security` - 🔒 安全漏洞
- `enhancement` - ✨ 改进
- `documentation` - 📚 文档

### 模块标签
- `backend` - 后端
- `frontend` - 前端
- `database` - 数据库
- `testing` - 测试
- `ci-cd` - CI/CD

### 状态标签
- `in-progress` - 进行中
- `blocked` - 阻塞
- `needs-review` - 待审核
- `wontfix` - 不修复

---

## 👥 角色职责

### 研发主管（dev-lead）
- 流程管理
- 审核代码
- 合并 PR
- 跟踪进度
- 跨团队协调

### 测试工程师（qa-engineer）
- 执行测试
- **创建 Issue**
- 验证修复
- **关闭 Issue**
- 维护测试报告

### 后端工程师（backend-dev）
- 领取后端 Issue
- 修复 bug
- 编写测试
- 提交 PR

### 前端工程师（frontend-dev）
- 领取前端 Issue
- 修复 bug
- 编写测试
- 提交 PR

### 架构师（architect）
- 架构问题处理
- 复杂 PR 审核
- 技术方案评审

---

## 📈 流程图

```
┌─────────────────────┐
│  qa-engineer        │
│  测试发现 Bug       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  qa-engineer        │
│  创建 GitHub Issue  │ ◄─── 谁发现谁创建
│  + 标签             │
│  + 优先级           │
│  + 分配负责人       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  开发 agent         │
│  领取 Issue         │
│  创建分支           │
│  bugfix/BUG-XXX     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  开发 agent         │
│  修复 bug           │
│  编写测试           │
│  Commit + Push      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  开发 agent         │
│  提交 Pull Request  │
│  关联 Issue         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  dev-lead/architect │
│  审核代码           │
│  Approve/Reject     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  CI/CD              │
│  自动测试           │
│  代码检查           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  dev-lead           │
│  合并到 main        │
│  删除分支           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  qa-engineer        │
│  验证修复           │ ◄─── 谁创建谁验证
│  关闭 Issue         │
└─────────────────────┘
```

---

## 🔗 相关文档

- [测试报告](../../workspace-qa-engineer/docs/TEST_REPORT.md)
- [Bug 列表](../../workspace-qa-engineer/docs/BUG_LIST.md)
- [执行摘要](../../workspace-qa-engineer/docs/EXECUTIVE_SUMMARY.md)

---

## 📝 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| 1.0 | 2026-02-16 | 初始版本，定义完整流程 | dev-lead |

---

**最后更新**: 2026-02-16 05:15 UTC
