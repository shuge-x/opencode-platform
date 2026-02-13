"""
Agent执行任务
"""
import asyncio
import json
from typing import Optional
from celery import current_task
from tasks.celery_app import celery_app
from app.utils.opencode_sidecar import OpenCodeSidecar
from app.core.security import get_current_user_id
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def execute_agent_task(
    self,
    prompt: str,
    session_id: str,
    user_id: str,
    timeout: int = 120
) -> dict:
    """
    异步执行Agent任务

    Args:
        prompt: 用户输入
        session_id: 会话ID
        user_id: 用户ID
        timeout: 超时时间（秒）

    Returns:
        执行结果
    """
    try:
        logger.info(f"Starting agent task {self.request.id} for user {user_id}")

        # 更新任务状态
        self.update_state(
            state='PROGRESS',
            meta={'status': 'executing', 'progress': 0}
        )

        # 创建Sidecar实例
        sidecar = OpenCodeSidecar()

        # 执行opencode
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            sidecar.execute(
                prompt=prompt,
                session_id=session_id,
                user_id=user_id,
                timeout=timeout
            )
        )

        # 更新任务状态
        self.update_state(
            state='PROGRESS',
            meta={'status': 'completed', 'progress': 100}
        )

        logger.info(f"Agent task {self.request.id} completed successfully")

        return {
            'success': True,
            'task_id': self.request.id,
            'output': result.get('output', ''),
            'session_id': session_id,
            'user_id': user_id
        }

    except asyncio.TimeoutError as e:
        logger.error(f"Agent task {self.request.id} timeout")
        self.update_state(
            state='FAILURE',
            meta={'error': 'Task timeout', 'detail': str(e)}
        )
        raise self.retry(exc=e, countdown=60)

    except Exception as e:
        logger.error(f"Agent task {self.request.id} failed: {e}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise self.retry(exc=e, countdown=60)


@celery_app.task
def health_check() -> dict:
    """
    健康检查任务
    """
    return {
        'status': 'healthy',
        'worker': current_task.request.hostname
    }
