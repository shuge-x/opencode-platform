"""
测试调试功能
"""
import asyncio
import json
import pytest
from app.core.debug_manager import DebugConnectionManager, DebugState


@pytest.mark.asyncio
async def test_debug_manager():
    """测试调试管理器"""
    manager = DebugConnectionManager()
    
    # 创建调试会话
    session = await manager.create_debug_session(
        session_id="test_session",
        execution_id=1,
        skill_id=1,
        user_id=1
    )
    
    assert session.session_id == "test_session"
    assert session.execution_id == 1
    assert session.state == DebugState.IDLE
    
    # 添加断点
    await manager.add_breakpoint(1, "main.py", 10)
    assert "main.py" in session.breakpoints
    assert len(session.breakpoints["main.py"]) == 1
    assert session.breakpoints["main.py"][0].line == 10
    
    # 移除断点
    await manager.remove_breakpoint(1, "main.py", 10)
    assert len(session.breakpoints["main.py"]) == 0
    
    # 测试暂停/继续
    await manager.pause_execution(1)
    assert session.state == DebugState.PAUSED
    
    await manager.resume_execution(1)
    assert session.state == DebugState.RUNNING
    
    # 测试单步执行
    await manager.step_execution(1)
    assert session.state == DebugState.RUNNING
    assert session.step_mode is True
    
    # 测试停止
    await manager.stop_execution(1)
    assert session.state == DebugState.STOPPED


@pytest.mark.asyncio
async def test_debug_manager_broadcast():
    """测试调试管理器广播功能"""
    manager = DebugConnectionManager()
    
    # 创建调试会话
    await manager.create_debug_session(
        session_id="test_session",
        execution_id=1,
        skill_id=1,
        user_id=1
    )
    
    # 测试发送日志
    # 注意：这里没有实际的WebSocket连接，所以只会更新会话状态
    await manager.send_log(1, "INFO", "Test log message")
    
    session = manager.get_debug_session(1)
    assert len(session.log_buffer) == 1
    assert session.log_buffer[0]["type"] == "log"
    assert session.log_buffer[0]["level"] == "INFO"
    assert session.log_buffer[0]["message"] == "Test log message"
    
    # 测试发送调试事件
    await manager.send_debug_event(
        1,
        event_type="breakpoint_hit",
        position={"file": "main.py", "line": 10},
        variables={"x": 1, "y": 2}
    )
    
    session = manager.get_debug_session(1)
    assert session.current_position == {"file": "main.py", "line": 10}
    assert session.variables == {"x": 1, "y": 2}
    
    # 测试发送错误
    await manager.send_error(
        1,
        error_type="ValueError",
        error_message="Test error",
        stack_trace="Test stack trace"
    )
    
    session = manager.get_debug_session(1)
    assert session.state == DebugState.ERROR


@pytest.mark.asyncio
async def test_should_pause():
    """测试断点检查"""
    manager = DebugConnectionManager()
    
    # 创建调试会话
    await manager.create_debug_session(
        session_id="test_session",
        execution_id=1,
        skill_id=1,
        user_id=1
    )
    
    # 添加断点
    await manager.add_breakpoint(1, "main.py", 10)
    
    # 检查应该暂停
    should_pause = await manager.should_pause(1, "main.py", 10)
    assert should_pause is True
    
    # 检查不应该暂停
    should_pause = await manager.should_pause(1, "main.py", 20)
    assert should_pause is False
    
    # 测试停止状态
    await manager.stop_execution(1)
    should_pause = await manager.should_pause(1, "main.py", 10)
    assert should_pause is True


@pytest.mark.asyncio
async def test_log_buffer_limit():
    """测试日志缓存限制"""
    manager = DebugConnectionManager()
    
    # 创建调试会话
    await manager.create_debug_session(
        session_id="test_session",
        execution_id=1,
        skill_id=1,
        user_id=1
    )
    
    # 发送超过1000条日志
    for i in range(1100):
        await manager.send_log(1, "INFO", f"Log message {i}")
    
    session = manager.get_debug_session(1)
    
    # 应该限制为500条（超过1000条后保留最近500条）
    assert len(session.log_buffer) == 500
    
    # 检查最后一条日志
    assert session.log_buffer[-1]["message"] == "Log message 1099"


if __name__ == "__main__":
    asyncio.run(test_debug_manager())
    asyncio.run(test_debug_manager_broadcast())
    asyncio.run(test_should_pause())
    asyncio.run(test_log_buffer_limit())
    print("All tests passed!")
