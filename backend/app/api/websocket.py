"""
WebSocket路由 - 实时通信
"""
import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.security import verify_token
from app.models.session import Session
from app.models.user import User
from app.schemas.session import Message
from tasks.agent_tasks import execute_agent_task
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # 存储活跃连接: {session_id: {user_id: WebSocket}}
        self.active_connections: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        """建立WebSocket连接"""
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}

        self.active_connections[session_id][user_id] = websocket
        logger.info(f"WebSocket connected: session={session_id}, user={user_id}")

    def disconnect(self, session_id: str, user_id: str):
        """断开WebSocket连接"""
        if session_id in self.active_connections:
            self.active_connections[session_id].pop(user_id, None)

            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

        logger.info(f"WebSocket disconnected: session={session_id}, user={user_id}")

    async def send_personal_message(self, message: dict, session_id: str, user_id: str):
        """发送个人消息"""
        if session_id in self.active_connections and user_id in self.active_connections[session_id]:
            websocket = self.active_connections[session_id][user_id]
            await websocket.send_json(message)

    async def broadcast(self, message: dict, session_id: str):
        """广播消息到会话中的所有用户"""
        if session_id in self.active_connections:
            for websocket in self.active_connections[session_id].values():
                await websocket.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/session/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket端点 - 实时对话

    Args:
        session_id: 会话ID
        token: JWT token（通过query参数传递）
        db: 数据库会话
    """
    # 验证token
    try:
        user_id = verify_token(token)
        if not user_id:
            await websocket.close(code=4001, reason="Unauthorized")
            return
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        await websocket.close(code=4001, reason="Unauthorized")
        return

    # 验证会话归属
    # 查询数据库验证 session_id 存在且属于该用户
    from sqlalchemy import select
    
    result = await db.execute(
        select(Session).where(
            Session.id == int(session_id),
            Session.user_id == int(user_id)
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        logger.warning(f"Session validation failed: session_id={session_id}, user_id={user_id}")
        await websocket.close(code=4004, reason="Session not found or access denied")
        return

    # 建立连接
    await manager.connect(websocket, session_id, user_id)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get('type')

                if message_type == 'chat':
                    # 处理对话消息
                    prompt = message.get('content', '')

                    # 提交Celery任务
                    task = execute_agent_task.delay(
                        prompt=prompt,
                        session_id=session_id,
                        user_id=user_id
                    )

                    # 发送任务已接收确认
                    await manager.send_personal_message(
                        {
                            'type': 'task_received',
                            'task_id': task.id,
                            'timestamp': datetime.utcnow().isoformat()
                        },
                        session_id,
                        user_id
                    )

                    # TODO: 轮询任务状态并推送更新
                    # 或者使用Celery的事件系统实时推送

                elif message_type == 'ping':
                    # 心跳检测
                    await manager.send_personal_message(
                        {'type': 'pong'},
                        session_id,
                        user_id
                    )

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON: {data}")
                await manager.send_personal_message(
                    {'type': 'error', 'message': 'Invalid message format'},
                    session_id,
                    user_id
                )

    except WebSocketDisconnect:
        manager.disconnect(session_id, user_id)
        logger.info(f"WebSocket disconnected normally: session={session_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id, user_id)
        await websocket.close(code=4000, reason=str(e))
