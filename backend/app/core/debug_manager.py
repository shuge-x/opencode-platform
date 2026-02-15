"""
调试管理器 - 管理技能调试会话
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class DebugState(str, Enum):
    """调试状态"""
    IDLE = "idle"  # 空闲
    RUNNING = "running"  # 运行中
    PAUSED = "paused"  # 已暂停
    STOPPED = "stopped"  # 已停止
    ERROR = "error"  # 错误


@dataclass
class Breakpoint:
    """断点"""
    file: str
    line: int
    condition: Optional[str] = None
    enabled: bool = True
    hit_count: int = 0


@dataclass
class DebugSession:
    """调试会话"""
    session_id: str
    execution_id: int
    skill_id: int
    user_id: int
    state: DebugState = DebugState.IDLE
    breakpoints: Dict[str, List[Breakpoint]] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    call_stack: List[Dict[str, Any]] = field(default_factory=list)
    current_position: Optional[Dict[str, Any]] = None
    log_buffer: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    # 暂停控制
    pause_event: Optional[asyncio.Event] = field(default=None)
    step_mode: bool = False  # 单步执行模式


class DebugConnectionManager:
    """调试WebSocket连接管理器"""

    def __init__(self):
        # 调试会话: {execution_id: DebugSession}
        self.debug_sessions: Dict[int, DebugSession] = {}
        # WebSocket连接: {execution_id: Set[WebSocket]}
        self.connections: Dict[int, Set[WebSocket]] = {}
        # 锁，防止并发问题
        self._locks: Dict[int, asyncio.Lock] = {}

    def _get_lock(self, execution_id: int) -> asyncio.Lock:
        """获取或创建锁"""
        if execution_id not in self._locks:
            self._locks[execution_id] = asyncio.Lock()
        return self._locks[execution_id]

    async def create_debug_session(
        self,
        session_id: str,
        execution_id: int,
        skill_id: int,
        user_id: int
    ) -> DebugSession:
        """创建调试会话"""
        async with self._get_lock(execution_id):
            if execution_id in self.debug_sessions:
                logger.warning(f"Debug session {execution_id} already exists")
                return self.debug_sessions[execution_id]

            debug_session = DebugSession(
                session_id=session_id,
                execution_id=execution_id,
                skill_id=skill_id,
                user_id=user_id,
                pause_event=asyncio.Event()
            )
            debug_session.pause_event.set()  # 初始状态为运行

            self.debug_sessions[execution_id] = debug_session
            self.connections[execution_id] = set()

            logger.info(f"Created debug session: execution_id={execution_id}")
            return debug_session

    async def connect(self, websocket: WebSocket, execution_id: int):
        """建立WebSocket连接"""
        await websocket.accept()
        
        async with self._get_lock(execution_id):
            if execution_id not in self.connections:
                self.connections[execution_id] = set()
            
            self.connections[execution_id].add(websocket)
            logger.info(f"WebSocket connected to debug session: execution_id={execution_id}")
            
            # 发送当前状态
            if execution_id in self.debug_sessions:
                session = self.debug_sessions[execution_id]
                await self._send_to_connection(websocket, {
                    'type': 'debug_status',
                    'state': session.state.value,
                    'position': session.current_position,
                    'variables': session.variables,
                    'call_stack': session.call_stack,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                # 发送缓存的日志
                for log in session.log_buffer[-50:]:  # 只发送最近50条
                    await self._send_to_connection(websocket, log)

    async def disconnect(self, websocket: WebSocket, execution_id: int):
        """断开WebSocket连接"""
        async with self._get_lock(execution_id):
            if execution_id in self.connections:
                self.connections[execution_id].discard(websocket)
                logger.info(f"WebSocket disconnected from debug session: execution_id={execution_id}")

    async def _send_to_connection(self, websocket: WebSocket, message: dict):
        """发送消息到单个连接"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def broadcast(self, execution_id: int, message: dict):
        """广播消息到所有连接"""
        async with self._get_lock(execution_id):
            if execution_id not in self.connections:
                return

            # 添加时间戳
            if 'timestamp' not in message:
                message['timestamp'] = datetime.utcnow().isoformat()

            # 发送到所有连接
            disconnected = set()
            for websocket in self.connections[execution_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to connection: {e}")
                    disconnected.add(websocket)

            # 清理断开的连接
            self.connections[execution_id] -= disconnected

    async def send_log(self, execution_id: int, log_level: str, message: str, metadata: Optional[Dict] = None):
        """发送日志事件"""
        log_event = {
            'type': 'log',
            'level': log_level,
            'message': message,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat()
        }

        # 缓存日志
        if execution_id in self.debug_sessions:
            session = self.debug_sessions[execution_id]
            session.log_buffer.append(log_event)
            # 限制缓存大小
            if len(session.log_buffer) > 1000:
                session.log_buffer = session.log_buffer[-500:]

        await self.broadcast(execution_id, log_event)

    async def send_debug_event(
        self,
        execution_id: int,
        event_type: str,
        position: Optional[Dict] = None,
        variables: Optional[Dict] = None,
        call_stack: Optional[List] = None,
        **kwargs
    ):
        """发送调试事件"""
        # 更新会话状态
        if execution_id in self.debug_sessions:
            session = self.debug_sessions[execution_id]
            
            if position:
                session.current_position = position
            if variables:
                session.variables.update(variables)
            if call_stack:
                session.call_stack = call_stack
            
            session.updated_at = datetime.utcnow()

        event = {
            'type': f'debug_{event_type}',
            'position': position,
            'variables': variables or {},
            'call_stack': call_stack or [],
            **kwargs,
            'timestamp': datetime.utcnow().isoformat()
        }

        await self.broadcast(execution_id, event)

    async def send_error(
        self,
        execution_id: int,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        position: Optional[Dict] = None
    ):
        """发送错误事件"""
        error_event = {
            'type': 'error',
            'error_type': error_type,
            'error_message': error_message,
            'stack_trace': stack_trace,
            'position': position,
            'timestamp': datetime.utcnow().isoformat()
        }

        # 更新会话状态
        if execution_id in self.debug_sessions:
            session = self.debug_sessions[execution_id]
            session.state = DebugState.ERROR
            session.updated_at = datetime.utcnow()

        await self.broadcast(execution_id, error_event)

    async def add_breakpoint(self, execution_id: int, file: str, line: int, condition: Optional[str] = None):
        """添加断点"""
        async with self._get_lock(execution_id):
            if execution_id not in self.debug_sessions:
                raise ValueError(f"Debug session {execution_id} not found")

            session = self.debug_sessions[execution_id]
            
            if file not in session.breakpoints:
                session.breakpoints[file] = []
            
            breakpoint = Breakpoint(file=file, line=line, condition=condition)
            session.breakpoints[file].append(breakpoint)

            await self.broadcast(execution_id, {
                'type': 'breakpoint_added',
                'file': file,
                'line': line,
                'condition': condition
            })

    async def remove_breakpoint(self, execution_id: int, file: str, line: int):
        """移除断点"""
        async with self._get_lock(execution_id):
            if execution_id not in self.debug_sessions:
                raise ValueError(f"Debug session {execution_id} not found")

            session = self.debug_sessions[execution_id]
            
            if file in session.breakpoints:
                session.breakpoints[file] = [
                    bp for bp in session.breakpoints[file] if bp.line != line
                ]

            await self.broadcast(execution_id, {
                'type': 'breakpoint_removed',
                'file': file,
                'line': line
            })

    async def pause_execution(self, execution_id: int):
        """暂停执行"""
        async with self._get_lock(execution_id):
            if execution_id not in self.debug_sessions:
                raise ValueError(f"Debug session {execution_id} not found")

            session = self.debug_sessions[execution_id]
            session.state = DebugState.PAUSED
            session.step_mode = False
            if session.pause_event:
                session.pause_event.clear()  # 阻塞执行

            await self.broadcast(execution_id, {
                'type': 'debug_paused',
                'state': DebugState.PAUSED.value
            })

    async def resume_execution(self, execution_id: int):
        """继续执行"""
        async with self._get_lock(execution_id):
            if execution_id not in self.debug_sessions:
                raise ValueError(f"Debug session {execution_id} not found")

            session = self.debug_sessions[execution_id]
            session.state = DebugState.RUNNING
            session.step_mode = False
            if session.pause_event:
                session.pause_event.set()  # 恢复执行

            await self.broadcast(execution_id, {
                'type': 'debug_resumed',
                'state': DebugState.RUNNING.value
            })

    async def step_execution(self, execution_id: int):
        """单步执行"""
        async with self._get_lock(execution_id):
            if execution_id not in self.debug_sessions:
                raise ValueError(f"Debug session {execution_id} not found")

            session = self.debug_sessions[execution_id]
            session.state = DebugState.RUNNING
            session.step_mode = True
            if session.pause_event:
                session.pause_event.set()  # 允许执行下一步

            await self.broadcast(execution_id, {
                'type': 'debug_stepping',
                'state': DebugState.RUNNING.value
            })

    async def stop_execution(self, execution_id: int):
        """停止执行"""
        async with self._get_lock(execution_id):
            if execution_id not in self.debug_sessions:
                raise ValueError(f"Debug session {execution_id} not found")

            session = self.debug_sessions[execution_id]
            session.state = DebugState.STOPPED
            if session.pause_event:
                session.pause_event.set()  # 唤醒但会检查状态

            await self.broadcast(execution_id, {
                'type': 'debug_stopped',
                'state': DebugState.STOPPED.value
            })

    def get_debug_session(self, execution_id: int) -> Optional[DebugSession]:
        """获取调试会话"""
        return self.debug_sessions.get(execution_id)

    async def should_pause(self, execution_id: int, file: str, line: int) -> bool:
        """检查是否应该暂停"""
        session = self.debug_sessions.get(execution_id)
        if not session:
            return False

        # 检查是否已停止
        if session.state == DebugState.STOPPED:
            return True

        # 检查断点
        if file in session.breakpoints:
            for breakpoint in session.breakpoints[file]:
                if breakpoint.enabled and breakpoint.line == line:
                    # TODO: 检查条件表达式
                    breakpoint.hit_count += 1
                    return True

        return False

    async def wait_if_paused(self, execution_id: int):
        """如果暂停状态则等待"""
        session = self.debug_sessions.get(execution_id)
        if not session or not session.pause_event:
            return

        await session.pause_event.wait()

        # 单步执行后再次暂停
        if session.step_mode:
            session.state = DebugState.PAUSED
            session.step_mode = False
            session.pause_event.clear()
            await self.broadcast(execution_id, {
                'type': 'debug_paused',
                'state': DebugState.PAUSED.value,
                'reason': 'step_complete'
            })


# 全局调试管理器实例
debug_manager = DebugConnectionManager()
