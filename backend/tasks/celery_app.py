"""
Celery应用配置
"""
from celery import Celery
from app.config import settings

celery_app = Celery(
    'opencode_tasks',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['tasks.agent_tasks']
)

# Celery配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5分钟超时
    task_soft_time_limit=240,  # 4分钟软超时
    worker_prefetch_multiplier=1,  # 每次只取1个任务
    worker_max_tasks_per_child=50,  # 每个worker处理50个任务后重启
)
