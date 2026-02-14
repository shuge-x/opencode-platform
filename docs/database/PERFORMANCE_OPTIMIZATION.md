# 数据库性能优化

## 索引策略

### 1. 主键索引（自动创建）
- users.id
- sessions.id
- messages.id
- files.id
- skills.id
- apps.id
- tool_calls.id
- tool_execution_logs.id

### 2. 外键索引
```sql
-- 会话关联
CREATE INDEX idx_sessions_user_id ON sessions(user_id);

-- 消息关联
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_user_id ON messages(user_id);

-- 文件关联
CREATE INDEX idx_files_user_id ON files(user_id);

-- 工具调用关联
CREATE INDEX idx_tool_calls_session_id ON tool_calls(session_id);
CREATE INDEX idx_tool_calls_message_id ON tool_calls(message_id);
CREATE INDEX idx_tool_execution_logs_tool_call_id ON tool_execution_logs(tool_call_id);
```

### 3. 查询优化索引
```sql
-- 时间范围查询
CREATE INDEX idx_sessions_created_at ON sessions(created_at);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_files_created_at ON files(created_at);
CREATE INDEX idx_tool_calls_created_at ON tool_calls(created_at);

-- 状态过滤
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_tool_calls_status ON tool_calls(status);

-- 文件名搜索
CREATE INDEX idx_files_filename ON files USING gin(to_tsvector('english', filename));

-- 工具名称搜索
CREATE INDEX idx_tool_calls_tool_name ON tool_calls(tool_name);
```

### 4. 复合索引（高频查询）
```sql
-- 用户会话列表
CREATE INDEX idx_sessions_user_created ON sessions(user_id, created_at DESC);

-- 会话消息列表
CREATE INDEX idx_messages_session_created ON messages(session_id, created_at ASC);

-- 用户文件列表
CREATE INDEX idx_files_user_created ON files(user_id, created_at DESC);

-- 工具调用历史
CREATE INDEX idx_tool_calls_session_status ON tool_calls(session_id, status, created_at DESC);
```

## 查询优化建议

### 1. 分页查询
```sql
-- 使用 LIMIT + OFFSET
SELECT * FROM messages
WHERE session_id = ?
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;

-- 或使用游标（更高效）
SELECT * FROM messages
WHERE session_id = ? AND created_at < ?
ORDER BY created_at DESC
LIMIT 20;
```

### 2. 避免 SELECT *
```sql
-- 不推荐
SELECT * FROM users;

-- 推荐
SELECT id, username, email FROM users;
```

### 3. 批量操作
```sql
-- 批量插入
INSERT INTO messages (session_id, content) VALUES
(1, 'msg1'),
(1, 'msg2'),
(1, 'msg3');

-- 批量更新
UPDATE messages SET status = 'read'
WHERE session_id = 1 AND status = 'unread';
```

## 连接池配置

```python
# SQLAlchemy 异步引擎配置
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # 连接池大小
    max_overflow=10,       # 最大溢出连接数
    pool_pre_ping=True,    # 连接健康检查
    pool_recycle=3600      # 连接回收时间（1小时）
)
```

## 缓存策略

### 1. Redis 缓存
- 用户信息（TTL: 1小时）
- 会话列表（TTL: 5分钟）
- 文件元数据（TTL: 30分钟）

### 2. 查询缓存
```python
# 使用 Redis 缓存查询结果
@cache(ttl=300)
async def get_user_sessions(user_id: int):
    # 查询数据库
    pass
```

## 监控指标

### 1. 慢查询日志
```sql
-- PostgreSQL 配置
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- 记录超过1秒的查询
```

### 2. 性能指标
- 平均查询时间
- 慢查询数量
- 连接池使用率
- 缓存命中率

## 优化检查清单

- [ ] 所有外键都有索引
- [ ] 高频查询字段有索引
- [ ] 复合查询有复合索引
- [ ] 分页查询使用索引
- [ ] 避免 N+1 查询
- [ ] 使用连接池
- [ ] 配置缓存
- [ ] 启用慢查询日志
