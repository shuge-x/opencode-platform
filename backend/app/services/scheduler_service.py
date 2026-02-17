"""
工作流调度服务

负责管理定时任务的调度，与 Celery Beat 集成
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json
import secrets
from croniter import croniter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.workflow import Workflow
from app.models.workflow_execution import TriggerType
from app.config import settings

logger = logging.getLogger(__name__)


class ScheduledTask:
    """定时任务数据类"""
    
    def __init__(
        self,
        workflow_id: int,
        cron: str,
        task_name: str,
        enabled: bool = True,
        next_run_time: Optional[datetime] = None,
        last_run_time: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.workflow_id = workflow_id
        self.cron = cron
        self.task_name = task_name
        self.enabled = enabled
        self.next_run_time = next_run_time
        self.last_run_time = last_run_time
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "cron": self.cron,
            "task_name": self.task_name,
            "enabled": self.enabled,
            "next_run_time": self.next_run_time.isoformat() if self.next_run_time else None,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledTask":
        return cls(
            workflow_id=data["workflow_id"],
            cron=data["cron"],
            task_name=data["task_name"],
            enabled=data.get("enabled", True),
            next_run_time=datetime.fromisoformat(data["next_run_time"]) if data.get("next_run_time") else None,
            last_run_time=datetime.fromisoformat(data["last_run_time"]) if data.get("last_run_time") else None,
            metadata=data.get("metadata", {})
        )


class WorkflowScheduler:
    """
    工作流调度器
    
    负责：
    - 管理定时任务的添加/删除
    - 与 Celery Beat 集成
    - 计算下次执行时间
    """
    
    # 调度任务存储 key 前缀（Redis）
    SCHEDULE_KEY_PREFIX = "workflow_schedule:"
    SCHEDULE_LIST_KEY = "workflow_schedules"
    
    def __init__(self, db_session: AsyncSession = None, redis_client = None):
        self.db = db_session
        self._redis = redis_client
        self._schedule_cache: Dict[int, ScheduledTask] = {}
    
    @property
    def redis(self):
        """延迟加载 Redis 客户端"""
        if self._redis is None:
            import redis.asyncio as redis
            self._redis = redis.from_url(settings.REDIS_URL)
        return self._redis
    
    async def schedule_workflow(
        self,
        workflow_id: int,
        cron: str,
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ScheduledTask:
        """
        调度工作流
        
        Args:
            workflow_id: 工作流 ID
            cron: Cron 表达式
            user_id: 用户 ID（可选）
            metadata: 额外元数据
            
        Returns:
            ScheduledTask: 创建的定时任务
            
        Raises:
            ValueError: Cron 表达式无效
        """
        # 验证 Cron 表达式
        if not self.validate_cron(cron):
            raise ValueError(f"Invalid cron expression: {cron}")
        
        # 检查工作流是否存在
        if self.db:
            result = await self.db.execute(
                select(Workflow).where(Workflow.id == workflow_id)
            )
            workflow = result.scalar_one_or_none()
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            # 更新工作流的触发配置
            workflow.trigger_config = {
                "type": TriggerType.SCHEDULED.value,
                "cron": cron,
                "enabled": True
            }
            if user_id:
                workflow.trigger_config["user_id"] = user_id
            await self.db.commit()
        
        # 创建任务名称
        task_name = f"workflow_{workflow_id}_scheduled"
        
        # 计算下次执行时间
        next_run_time = self.get_next_run_time(cron)
        
        # 创建定时任务
        task = ScheduledTask(
            workflow_id=workflow_id,
            cron=cron,
            task_name=task_name,
            enabled=True,
            next_run_time=next_run_time,
            metadata={
                "user_id": user_id,
                **(metadata or {})
            }
        )
        
        # 存储到 Redis
        await self._save_schedule(task)
        
        # 添加到 Celery Beat
        await self._add_to_celery_beat(task)
        
        # 更新缓存
        self._schedule_cache[workflow_id] = task
        
        logger.info(f"Scheduled workflow {workflow_id} with cron '{cron}', next run: {next_run_time}")
        
        return task
    
    async def unschedule_workflow(self, workflow_id: int) -> bool:
        """
        取消工作流调度
        
        Args:
            workflow_id: 工作流 ID
            
        Returns:
            bool: 是否成功取消
        """
        # 从 Redis 获取现有调度
        task = await self.get_scheduled_task(workflow_id)
        
        if not task:
            logger.warning(f"No schedule found for workflow {workflow_id}")
            return False
        
        # 从 Redis 删除
        await self._delete_schedule(workflow_id)
        
        # 从 Celery Beat 移除
        await self._remove_from_celery_beat(task)
        
        # 更新工作流的触发配置
        if self.db:
            result = await self.db.execute(
                select(Workflow).where(Workflow.id == workflow_id)
            )
            workflow = result.scalar_one_or_none()
            if workflow and workflow.trigger_config:
                workflow.trigger_config["enabled"] = False
                await self.db.commit()
        
        # 清除缓存
        if workflow_id in self._schedule_cache:
            del self._schedule_cache[workflow_id]
        
        logger.info(f"Unscheduled workflow {workflow_id}")
        
        return True
    
    async def get_scheduled_task(self, workflow_id: int) -> Optional[ScheduledTask]:
        """
        获取指定工作流的调度任务
        
        Args:
            workflow_id: 工作流 ID
            
        Returns:
            ScheduledTask 或 None
        """
        # 先查缓存
        if workflow_id in self._schedule_cache:
            return self._schedule_cache[workflow_id]
        
        # 从 Redis 获取
        task_data = await self.redis.get(f"{self.SCHEDULE_KEY_PREFIX}{workflow_id}")
        
        if task_data:
            task = ScheduledTask.from_dict(json.loads(task_data))
            self._schedule_cache[workflow_id] = task
            return task
        
        return None
    
    async def get_scheduled_workflows(self) -> List[ScheduledTask]:
        """
        获取所有已调度的工作流
        
        Returns:
            List[ScheduledTask]: 所有调度任务列表
        """
        # 从 Redis 获取所有工作流 ID
        workflow_ids = await self.redis.smembers(self.SCHEDULE_LIST_KEY)
        
        tasks = []
        for wid_bytes in workflow_ids:
            workflow_id = int(wid_bytes)
            task = await self.get_scheduled_task(workflow_id)
            if task:
                tasks.append(task)
        
        return tasks
    
    async def update_schedule(
        self,
        workflow_id: int,
        cron: Optional[str] = None,
        enabled: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ScheduledTask]:
        """
        更新调度配置
        
        Args:
            workflow_id: 工作流 ID
            cron: 新的 Cron 表达式（可选）
            enabled: 是否启用（可选）
            metadata: 新的元数据（可选）
            
        Returns:
            更新后的 ScheduledTask 或 None
        """
        task = await self.get_scheduled_task(workflow_id)
        
        if not task:
            logger.warning(f"No schedule found for workflow {workflow_id}")
            return None
        
        # 更新字段
        if cron is not None:
            if not self.validate_cron(cron):
                raise ValueError(f"Invalid cron expression: {cron}")
            task.cron = cron
            task.next_run_time = self.get_next_run_time(cron)
        
        if enabled is not None:
            task.enabled = enabled
        
        if metadata is not None:
            task.metadata.update(metadata)
        
        # 保存更新
        await self._save_schedule(task)
        
        # 更新 Celery Beat
        if cron is not None or enabled is not None:
            await self._update_celery_beat(task)
        
        # 更新缓存
        self._schedule_cache[workflow_id] = task
        
        logger.info(f"Updated schedule for workflow {workflow_id}")
        
        return task
    
    async def enable_schedule(self, workflow_id: int) -> bool:
        """启用调度"""
        task = await self.update_schedule(workflow_id, enabled=True)
        return task is not None
    
    async def disable_schedule(self, workflow_id: int) -> bool:
        """禁用调度"""
        task = await self.update_schedule(workflow_id, enabled=False)
        return task is not None
    
    @staticmethod
    def validate_cron(cron: str) -> bool:
        """
        验证 Cron 表达式
        
        Args:
            cron: Cron 表达式
            
        Returns:
            bool: 是否有效
        """
        try:
            croniter(cron)
            return True
        except (ValueError, KeyError):
            return False
    
    @staticmethod
    def get_next_run_time(cron: str, base_time: Optional[datetime] = None) -> datetime:
        """
        获取下次执行时间
        
        Args:
            cron: Cron 表达式
            base_time: 基准时间（默认为当前时间）
            
        Returns:
            datetime: 下次执行时间
        """
        if base_time is None:
            base_time = datetime.utcnow()
        
        iter = croniter(cron, base_time)
        return iter.get_next(datetime)
    
    async def _save_schedule(self, task: ScheduledTask) -> None:
        """保存调度到 Redis"""
        key = f"{self.SCHEDULE_KEY_PREFIX}{task.workflow_id}"
        
        # 保存任务数据
        await self.redis.set(key, json.dumps(task.to_dict()))
        
        # 添加到列表
        await self.redis.sadd(self.SCHEDULE_LIST_KEY, task.workflow_id)
    
    async def _delete_schedule(self, workflow_id: int) -> None:
        """从 Redis 删除调度"""
        key = f"{self.SCHEDULE_KEY_PREFIX}{workflow_id}"
        
        await self.redis.delete(key)
        await self.redis.srem(self.SCHEDULE_LIST_KEY, workflow_id)
    
    async def _add_to_celery_beat(self, task: ScheduledTask) -> None:
        """
        添加任务到 Celery Beat
        
        Celery Beat 的动态调度需要通过 Django-Celery-Beat 或
        直接操作 celerybeat-schedule 文件来实现
        """
        from tasks.celery_app import celery_app
        
        # 添加到 Celery Beat 配置
        schedule_name = f"workflow_{task.workflow_id}_schedule"
        
        # 使用 Celery 的 add_periodic_task（如果可用）
        # 或者直接操作 schedule
        try:
            from celery.schedules import crontab
            
            # 解析 cron 表达式
            parts = task.cron.split()
            if len(parts) == 5:
                minute, hour, day_of_month, month_of_year, day_of_week = parts
                
                # 添加周期性任务
                celery_app.add_periodic_task(
                    crontab(
                        minute=minute,
                        hour=hour,
                        day_of_month=day_of_month,
                        month_of_year=month_of_year,
                        day_of_week=day_of_week
                    ),
                    "tasks.workflow_tasks.execute_scheduled_workflow",
                    args=(task.workflow_id,),
                    name=schedule_name,
                    options={"queue": "workflows"}
                )
                
                logger.info(f"Added periodic task {schedule_name} to Celery Beat")
        except Exception as e:
            logger.error(f"Failed to add task to Celery Beat: {e}")
            # 即使 Celery Beat 配置失败，Redis 中的调度仍然有效
            # 可以通过其他方式（如独立调度服务）来处理
    
    async def _remove_from_celery_beat(self, task: ScheduledTask) -> None:
        """从 Celery Beat 移除任务"""
        from tasks.celery_app import celery_app
        
        schedule_name = f"workflow_{task.workflow_id}_schedule"
        
        try:
            # Celery 5.x 的 API
            if hasattr(celery_app, 'cancel') and hasattr(celery_app, 'periodic_tasks'):
                celery_app.cancel(schedule_name)
            else:
                # 对于旧版本，直接从 conf 中移除
                if hasattr(celery_app.conf, 'beat_schedule'):
                    if schedule_name in celery_app.conf.beat_schedule:
                        del celery_app.conf.beat_schedule[schedule_name]
            
            logger.info(f"Removed periodic task {schedule_name} from Celery Beat")
        except Exception as e:
            logger.error(f"Failed to remove task from Celery Beat: {e}")
    
    async def _update_celery_beat(self, task: ScheduledTask) -> None:
        """更新 Celery Beat 中的任务"""
        # 先移除旧的，再添加新的
        await self._remove_from_celery_beat(task)
        if task.enabled:
            await self._add_to_celery_beat(task)


class WebhookTokenManager:
    """
    Webhook Token 管理器
    
    负责：
    - 生成唯一 token
    - 验证 token
    - 管理 token 与工作流的映射
    """
    
    WEBHOOK_TOKEN_PREFIX = "webhook_token:"
    WEBHOOK_TOKEN_LIST = "webhook_tokens"
    
    def __init__(self, redis_client=None):
        self._redis = redis_client
    
    @property
    def redis(self):
        if self._redis is None:
            import redis.asyncio as redis
            self._redis = redis.from_url(settings.REDIS_URL)
        return self._redis
    
    async def generate_token(self, workflow_id: int) -> str:
        """
        为工作流生成 webhook token
        
        Args:
            workflow_id: 工作流 ID
            
        Returns:
            str: 生成的 token
        """
        # 生成安全随机 token
        token = secrets.token_urlsafe(32)
        
        # 存储映射
        await self.redis.set(
            f"{self.WEBHOOK_TOKEN_PREFIX}{token}",
            str(workflow_id)
        )
        
        # 添加到列表
        await self.redis.sadd(self.WEBHOOK_TOKEN_LIST, token)
        
        logger.info(f"Generated webhook token for workflow {workflow_id}")
        
        return token
    
    async def validate_token(self, token: str) -> Optional[int]:
        """
        验证 webhook token
        
        Args:
            token: Webhook token
            
        Returns:
            int: 工作流 ID，如果无效返回 None
        """
        workflow_id = await self.redis.get(f"{self.WEBHOOK_TOKEN_PREFIX}{token}")
        
        if workflow_id:
            return int(workflow_id)
        
        return None
    
    async def revoke_token(self, token: str) -> bool:
        """
        撤销 webhook token
        
        Args:
            token: 要撤销的 token
            
        Returns:
            bool: 是否成功
        """
        result = await self.redis.delete(f"{self.WEBHOOK_TOKEN_PREFIX}{token}")
        await self.redis.srem(self.WEBHOOK_TOKEN_LIST, token)
        
        return result > 0
    
    async def revoke_workflow_tokens(self, workflow_id: int) -> int:
        """
        撤销工作流的所有 tokens
        
        Args:
            workflow_id: 工作流 ID
            
        Returns:
            int: 撤销的 token 数量
        """
        revoked = 0
        tokens = await self.redis.smembers(self.WEBHOOK_TOKEN_LIST)
        
        for token_bytes in tokens:
            token = token_bytes.decode() if isinstance(token_bytes, bytes) else token_bytes
            wid = await self.validate_token(token)
            if wid == workflow_id:
                await self.revoke_token(token)
                revoked += 1
        
        return revoked
    
    async def get_workflow_by_token(self, token: str) -> Optional[int]:
        """
        根据 token 获取工作流 ID
        
        Args:
            token: Webhook token
            
        Returns:
            int: 工作流 ID 或 None
        """
        return await self.validate_token(token)


# 导出
__all__ = [
    "WorkflowScheduler",
    "ScheduledTask",
    "WebhookTokenManager"
]
