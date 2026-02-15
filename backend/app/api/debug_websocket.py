"""
调试 WebSocket 路由 - 技能调试控制台
"""
import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.security import verify_token
from app.models.skill import SkillExecution
from app.core.debug_manager import debug_manager, DebugState
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/debug/{execution_id}")
async def debug_websocket_endpoint(
    websocket: WebSocket,
    execution_id: int,
    token: str = Query(...)
):
    """
    调试 WebSocket 端点

    Args:
        execution_id: 技能执行ID
        token: JWT token（通过query参数传递）
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

    # 验证执行ID和权限
    # TODO: 查询数据库验证execution_id存在且属于该用户

    # 建立连接
    await debug_manager.connect(websocket, execution_id)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get('type')

                # 处理不同类型的消息
                if message_type == 'ping':
                    # 心跳检测
                    await debug_manager._send_to_connection(websocket, {
                        'type': 'pong',
                        'timestamp': datetime.utcnow().isoformat()
                    })

                elif message_type == 'add_breakpoint':
                    # 添加断点
                    file = message.get('file')
                    line = message.get('line')
                    condition = message.get('condition')
                    
                    if file and line:
                        await debug_manager.add_breakpoint(
                            execution_id,
                            file,
                            line,
                            condition
                        )

                elif message_type == 'remove_breakpoint':
                    # 移除断点
                    file = message.get('file')
                    line = message.get('line')
                    
                    if file and line:
                        await debug_manager.remove_breakpoint(
                            execution_id,
                            file,
                            line
                        )

                elif message_type == 'pause':
                    # 暂停执行
                    await debug_manager.pause_execution(execution_id)

                elif message_type == 'resume':
                    # 继续执行
                    await debug_manager.resume_execution(execution_id)

                elif message_type == 'step':
                    # 单步执行
                    await debug_manager.step_execution(execution_id)

                elif message_type == 'stop':
                    # 停止执行
                    await debug_manager.stop_execution(execution_id)

                elif message_type == 'get_variables':
                    # 获取变量
                    session = debug_manager.get_debug_session(execution_id)
                    if session:
                        await debug_manager._send_to_connection(websocket, {
                            'type': 'variables',
                            'variables': session.variables,
                            'timestamp': datetime.utcnow().isoformat()
                        })

                elif message_type == 'get_call_stack':
                    # 获取调用栈
                    session = debug_manager.get_debug_session(execution_id)
                    if session:
                        await debug_manager._send_to_connection(websocket, {
                            'type': 'call_stack',
                            'call_stack': session.call_stack,
                            'timestamp': datetime.utcnow().isoformat()
                        })

                elif message_type == 'evaluate':
                    # 计算表达式
                    expression = message.get('expression')
                    # TODO: 实现表达式计算
                    await debug_manager._send_to_connection(websocket, {
                        'type': 'evaluation_result',
                        'expression': expression,
                        'result': None,
                        'error': 'Expression evaluation not implemented yet',
                        'timestamp': datetime.utcnow().isoformat()
                    })

                else:
                    logger.warning(f"Unknown message type: {message_type}")
                    await debug_manager._send_to_connection(websocket, {
                        'type': 'error',
                        'message': f'Unknown message type: {message_type}',
                        'timestamp': datetime.utcnow().isoformat()
                    })

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON: {data}")
                await debug_manager._send_to_connection(websocket, {
                    'type': 'error',
                    'message': 'Invalid message format',
                    'timestamp': datetime.utcnow().isoformat()
                })

            except ValueError as e:
                logger.error(f"Debug operation failed: {e}")
                await debug_manager._send_to_connection(websocket, {
                    'type': 'error',
                    'message': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })

            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                await debug_manager._send_to_connection(websocket, {
                    'type': 'error',
                    'message': 'Internal server error',
                    'timestamp': datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        await debug_manager.disconnect(websocket, execution_id)
        logger.info(f"Debug WebSocket disconnected normally: execution_id={execution_id}")

    except Exception as e:
        logger.error(f"Debug WebSocket error: {e}", exc_info=True)
        await debug_manager.disconnect(websocket, execution_id)
        await websocket.close(code=4000, reason=str(e))


@router.post("/debug/{execution_id}/start")
async def start_debug_session(
    execution_id: int,
    session_id: str,
    skill_id: int,
    user_id: int = Depends(verify_token)
):
    """
    启动调试会话

    在技能执行开始前调用，创建调试会话
    """
    try:
        debug_session = await debug_manager.create_debug_session(
            session_id=session_id,
            execution_id=execution_id,
            skill_id=skill_id,
            user_id=user_id
        )

        return {
            "success": True,
            "execution_id": execution_id,
            "state": debug_session.state.value
        }

    except Exception as e:
        logger.error(f"Failed to start debug session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/{execution_id}/status")
async def get_debug_status(
    execution_id: int,
    user_id: int = Depends(verify_token)
):
    """
    获取调试状态
    """
    session = debug_manager.get_debug_session(execution_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Debug session not found")

    return {
        "execution_id": execution_id,
        "state": session.state.value,
        "current_position": session.current_position,
        "breakpoints": {
            file: [{"line": bp.line, "condition": bp.condition, "enabled": bp.enabled}
                   for bp in breakpoints]
            for file, breakpoints in session.breakpoints.items()
        },
        "variables": session.variables,
        "call_stack": session.call_stack,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat()
    }
