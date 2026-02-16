"""
WebSocket路由 - 实时通信
"""
import json
import logging
import asyncio
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
from app.config import settings

logger = logging.getLogger(__name__)

# 心跳超时配置（秒）
HEARTBEAT_TIMEOUT = getattr(settings, 'WS_HEARTBEAT_TIMEOUT', 60)
HEARTBEAT_INTERVAL = getattr(settings, 'WS_HEARTBEAT_INTERVAL', 30)


def submit_celery_task_safe(task_func, *args, **kwargs):
    """
    安全提交 Celery 任务，包含错误处理和日志记录
    
    Returns:
        AsyncResult or None: 任务结果对象，失败时返回 None
    """
    try:
        task = task_func.delay(*args, **kwargs)
        logger.info(f"Celery task submitted via WebSocket: {task.id}")
        return task
    except Exception as e:
        logger.error(f"Failed to submit Celery task via WebSocket: {e}")
        return None


router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # 存储活跃连接: {session_id: {user_id: {"websocket": WebSocket, "last_activity": datetime}}}
        self.active_connections: dict[str, dict[str, dict]] = {}

    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        """建立WebSocket连接"""
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}

        self.active_connections[session_id][user_id] = {
            "websocket": websocket,
            "last_activity": datetime.utcnow()
        }
        logger.info(f"WebSocket connected: session={session_id}, user={user_id}")

    def disconnect(self, session_id: str, user_id: str, reason: str = "normal"):
        """断开WebSocket连接"""
        if session_id in self.active_connections:
            self.active_connections[session_id].pop(user_id, None)

            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

        logger.info(f"WebSocket disconnected: session={session_id}, user={user_id}, reason={reason}")

    def update_activity(self, session_id: str, user_id: str):
        """更新最后活动时间"""
        if session_id in self.active_connections and user_id in self.active_connections[session_id]:
            self.active_connections[session_id][user_id]["last_activity"] = datetime.utcnow()

    def get_last_activity(self, session_id: str, user_id: str) -> Optional[datetime]:
        """获取最后活动时间"""
        if session_id in self.active_connections and user_id in self.active_connections[session_id]:
            return self.active_connections[session_id][user_id]["last_activity"]
        return None

    async def send_personal_message(self, message: dict, session_id: str, user_id: str):
        """发送个人消息"""
        if session_id in self.active_connections and user_id in self.active_connections[session_id]:
            websocket = self.active_connections[session_id][user_id]["websocket"]
            await websocket.send_json(message)

    async def broadcast(self, message: dict, session_id: str):
        """广播消息到会话中的所有用户"""
        if session_id in self.active_connections:
            for conn_data in self.active_connections[session_id].values():
                await conn_data["websocket"].send_json(message)


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

    # 心跳任务
    async def heartbeat_task():
        """定期发送心跳检测"""
        try:
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                
                # 检查是否超时
                last_activity = manager.get_last_activity(session_id, user_id)
                if last_activity:
                    idle_seconds = (datetime.utcnow() - last_activity).total_seconds()
                    
                    if idle_seconds > HEARTBEAT_TIMEOUT:
                        logger.warning(
                            f"WebSocket heartbeat timeout: session={session_id}, "
                            f"user_id={user_id}, idle_seconds={idle_seconds:.1f}"
                        )
                        await websocket.close(code=4002, reason="Heartbeat timeout")
                        return
                    
                    # 发送心跳 ping
                    try:
                        await manager.send_personal_message(
                            {'type': 'ping', 'timestamp': datetime.utcnow().isoformat()},
                            session_id,
                            user_id
                        )
                    except Exception as e:
                        logger.error(f"Failed to send heartbeat: {e}")
                        return
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Heartbeat task error: {e}")

    # 启动心跳任务
    heartbeat = asyncio.create_task(heartbeat_task())

    try:
        while True:
            # 使用超时接收消息
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=HEARTBEAT_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.warning(
                    f"WebSocket receive timeout: session={session_id}, "
                    f"user_id={user_id}, timeout={HEARTBEAT_TIMEOUT}s"
                )
                await websocket.close(code=4002, reason="Connection timeout")
                break
            
            # 更新活动时间
            manager.update_activity(session_id, user_id)

            try:
                message = json.loads(data)
                message_type = message.get('type')

                if message_type == 'chat':
                    # 处理对话消息
                    prompt = message.get('content', '')

                    # 提交Celery任务（带错误处理）
                    task = submit_celery_task_safe(
                        execute_agent_task,
                        prompt=prompt,
                        session_id=session_id,
                        user_id=user_id
                    )
                    
                    if not task:
                        # 任务提交失败，通知用户
                        await manager.send_personal_message(
                            {
                                'type': 'error',
                                'message': 'Task processing service unavailable',
                                'timestamp': datetime.utcnow().isoformat()
                            },
                            session_id,
                            user_id
                        )
                        continue

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

                    # 任务状态推送：可通过轮询或Celery事件系统实现
                    # 或者使用Celery的事件系统实时推送

                elif message_type == 'pong':
                    # 心跳响应 - 已通过 update_activity 更新时间
                    logger.debug(f"Heartbeat pong received: session={session_id}, user={user_id}")

                elif message_type == 'ping':
                    # 客户端发起的心跳
                    await manager.send_personal_message(
                        {'type': 'pong', 'timestamp': datetime.utcnow().isoformat()},
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
        manager.disconnect(session_id, user_id, reason="client_disconnect")
        logger.info(f"WebSocket disconnected normally: session={session_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id, user_id, reason=f"error: {str(e)}")
        try:
            await websocket.close(code=4000, reason=str(e))
        except:
            pass
    finally:
        # 取消心跳任务
        heartbeat.cancel()
        try:
            await heartbeat
        except asyncio.CancelledError:
            pass
