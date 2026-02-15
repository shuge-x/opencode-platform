# 技能调试控制台 - 使用指南

## 概述

技能调试控制台提供了完整的调试功能，包括实时日志流、断点调试、变量监控和错误捕获。

## 功能特性

### 1. 实时日志流（WebSocket）

- 通过 WebSocket 连接到调试会话
- 实时接收技能执行日志
- 支持多个客户端同时连接
- 自动缓存最近1000条日志

### 2. 调试事件推送

- 捕获技能执行过程中的调试事件
- 推送断点命中、变量变化等事件
- 支持调试控制（暂停、继续、单步执行）
- 实时调用栈跟踪

### 3. 错误捕获

- 捕获技能执行中的异常
- 格式化错误堆栈信息
- 推送错误事件到前端
- 详细的错误类型和消息

## API 端点

### 1. 启动调试执行

```http
POST /api/skills/execution/execute/debug
Authorization: Bearer <token>
Content-Type: application/json

{
  "skill_id": 1,
  "input_params": {
    "param1": "value1"
  }
}
```

响应：
```json
{
  "id": 1,
  "skill_id": 1,
  "user_id": 1,
  "status": "pending",
  "input_params": {...},
  "created_at": "2026-02-15T04:21:00"
}
```

### 2. 启动调试会话

```http
POST /api/debug/{execution_id}/start
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_id": "debug_1",
  "skill_id": 1
}
```

### 3. 获取调试状态

```http
GET /api/debug/{execution_id}/status
Authorization: Bearer <token>
```

响应：
```json
{
  "execution_id": 1,
  "state": "paused",
  "current_position": {
    "file": "main.py",
    "line": 10
  },
  "breakpoints": {
    "main.py": [
      {"line": 10, "condition": null, "enabled": true}
    ]
  },
  "variables": {
    "x": 1,
    "y": 2
  },
  "call_stack": [...]
}
```

## WebSocket 连接

### 连接 URL

```
ws://localhost:8000/ws/debug/{execution_id}?token={jwt_token}
```

### 消息格式

所有消息均为 JSON 格式。

#### 客户端 → 服务端

##### 1. 心跳检测
```json
{
  "type": "ping"
}
```

##### 2. 添加断点
```json
{
  "type": "add_breakpoint",
  "file": "main.py",
  "line": 10,
  "condition": "x > 5"
}
```

##### 3. 移除断点
```json
{
  "type": "remove_breakpoint",
  "file": "main.py",
  "line": 10
}
```

##### 4. 暂停执行
```json
{
  "type": "pause"
}
```

##### 5. 继续执行
```json
{
  "type": "resume"
}
```

##### 6. 单步执行
```json
{
  "type": "step"
}
```

##### 7. 停止执行
```json
{
  "type": "stop"
}
```

##### 8. 获取变量
```json
{
  "type": "get_variables"
}
```

##### 9. 获取调用栈
```json
{
  "type": "get_call_stack"
}
```

#### 服务端 → 客户端

##### 1. 心跳响应
```json
{
  "type": "pong",
  "timestamp": "2026-02-15T04:21:00"
}
```

##### 2. 日志事件
```json
{
  "type": "log",
  "level": "INFO",
  "message": "Processing data...",
  "metadata": {},
  "timestamp": "2026-02-15T04:21:00"
}
```

##### 3. 调试状态
```json
{
  "type": "debug_status",
  "state": "paused",
  "position": {
    "file": "main.py",
    "line": 10
  },
  "variables": {...},
  "call_stack": [...],
  "timestamp": "2026-02-15T04:21:00"
}
```

##### 4. 断点命中事件
```json
{
  "type": "debug_breakpoint_hit",
  "position": {
    "file": "main.py",
    "line": 10
  },
  "variables": {...},
  "call_stack": [...],
  "timestamp": "2026-02-15T04:21:00"
}
```

##### 5. 断点已添加
```json
{
  "type": "breakpoint_added",
  "file": "main.py",
  "line": 10,
  "condition": "x > 5",
  "timestamp": "2026-02-15T04:21:00"
}
```

##### 6. 调试暂停
```json
{
  "type": "debug_paused",
  "state": "paused",
  "timestamp": "2026-02-15T04:21:00"
}
```

##### 7. 调试继续
```json
{
  "type": "debug_resumed",
  "state": "running",
  "timestamp": "2026-02-15T04:21:00"
}
```

##### 8. 执行完成
```json
{
  "type": "execution_completed",
  "status": "success",
  "output": "Result...",
  "timestamp": "2026-02-15T04:21:00"
}
```

##### 9. 错误事件
```json
{
  "type": "error",
  "error_type": "ValueError",
  "error_message": "Invalid value",
  "stack_trace": "...",
  "position": {
    "file": "main.py",
    "line": 15
  },
  "timestamp": "2026-02-15T04:21:00"
}
```

## 使用示例

### Python 客户端

```python
import asyncio
import websockets
import json

async def debug_client():
    token = "your_jwt_token"
    execution_id = 1
    uri = f"ws://localhost:8000/ws/debug/{execution_id}?token={token}"
    
    async with websockets.connect(uri) as websocket:
        # 添加断点
        await websocket.send(json.dumps({
            "type": "add_breakpoint",
            "file": "main.py",
            "line": 10
        }))
        
        # 监听事件
        while True:
            message = await websocket.recv()
            event = json.loads(message)
            
            print(f"Received event: {event['type']}")
            
            if event['type'] == 'debug_breakpoint_hit':
                print(f"Breakpoint hit at {event['position']}")
                print(f"Variables: {event['variables']}")
                
                # 继续执行
                await websocket.send(json.dumps({
                    "type": "resume"
                }))
            
            elif event['type'] == 'execution_completed':
                print(f"Execution completed with status: {event['status']}")
                break
            
            elif event['type'] == 'error':
                print(f"Error: {event['error_message']}")
                print(f"Stack trace: {event['stack_trace']}")
                break

asyncio.run(debug_client())
```

### JavaScript 客户端

```javascript
const token = 'your_jwt_token';
const executionId = 1;
const ws = new WebSocket(`ws://localhost:8000/ws/debug/${executionId}?token=${token}`);

ws.onopen = () => {
    console.log('Connected to debug session');
    
    // 添加断点
    ws.send(JSON.stringify({
        type: 'add_breakpoint',
        file: 'main.py',
        line: 10
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data.type);
    
    switch (data.type) {
        case 'debug_breakpoint_hit':
            console.log('Breakpoint hit:', data.position);
            console.log('Variables:', data.variables);
            
            // 继续执行
            ws.send(JSON.stringify({ type: 'resume' }));
            break;
            
        case 'execution_completed':
            console.log('Execution completed:', data.status);
            ws.close();
            break;
            
        case 'error':
            console.error('Error:', data.error_message);
            console.error('Stack trace:', data.stack_trace);
            break;
    }
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

ws.onclose = () => {
    console.log('Disconnected');
};
```

## 调试流程

1. **启动调试执行**
   - 调用 `/api/skills/execution/execute/debug` 启动调试执行
   - 获取 execution_id

2. **建立 WebSocket 连接**
   - 使用 execution_id 连接到调试 WebSocket
   - 连接时会自动发送当前状态和缓存日志

3. **设置断点**
   - 发送 `add_breakpoint` 消息设置断点
   - 可以设置条件断点

4. **监控执行**
   - 接收实时日志事件
   - 接收调试事件（断点命中、变量变化等）
   - 接收错误事件

5. **调试控制**
   - 使用 `pause` 暂停执行
   - 使用 `resume` 继续执行
   - 使用 `step` 单步执行
   - 使用 `stop` 停止执行

6. **查看状态**
   - 使用 `get_variables` 获取变量
   - 使用 `get_call_stack` 获取调用栈
   - 或从调试事件中获取这些信息

## 技术架构

### 调试管理器（DebugManager）

- 管理所有调试会话
- 处理 WebSocket 连接
- 推送调试事件
- 管理断点和调试控制

### 调试执行器（DebugExecutor）

- 扩展技能执行沙箱
- 在技能代码中插入调试钩子
- 流式传输容器日志
- 解析和转发调试事件

### 调试插桩

- 在技能代码中注入调试代码
- 捕获函数调用和行执行
- 发送调试事件到日志流
- 捕获和格式化错误

## 安全隔离

- 使用 Docker 容器隔离执行
- 禁用网络访问
- 限制内存和 CPU 使用
- 设置执行超时
- 用户权限验证

## 性能考虑

- 日志缓存限制为1000条
- 使用异步 I/O 处理 WebSocket
- 使用锁防止并发问题
- 容器执行异步等待

## 未来改进

- [ ] 支持条件断点表达式计算
- [ ] 支持变量修改
- [ ] 支持热重载
- [ ] 支持多线程调试
- [ ] 支持远程调试
- [ ] 优化大量日志的性能
