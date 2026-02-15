"""
技能调用监控 - Prometheus 指标

实现：
- 调用计数器
- 响应时间直方图
- 错误计数器
- 实时统计
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, Info
import time

logger = logging.getLogger(__name__)


# ============= Prometheus 指标定义 =============

# 技能调用计数器
SKILL_INVOCATIONS_TOTAL = Counter(
    'skill_invocations_total',
    'Total number of skill invocations',
    ['skill_id', 'skill_name', 'status', 'execution_type']
)

# 技能调用响应时间直方图
SKILL_INVOCATION_DURATION = Histogram(
    'skill_invocation_duration_seconds',
    'Duration of skill invocations in seconds',
    ['skill_id', 'skill_name', 'execution_type'],
    buckets=[0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 15.0, 30.0, 60.0]
)

# 技能执行错误计数器
SKILL_ERRORS_TOTAL = Counter(
    'skill_errors_total',
    'Total number of skill execution errors',
    ['skill_id', 'skill_name', 'error_type']
)

# 当前正在执行的技能数
SKILL_ACTIVE_EXECUTIONS = Gauge(
    'skill_active_executions',
    'Number of skill executions currently in progress',
    ['execution_type']
)

# 技能资源使用
SKILL_MEMORY_USAGE = Gauge(
    'skill_memory_usage_bytes',
    'Memory usage of skill executions',
    ['skill_id', 'skill_name']
)

SKILL_CPU_USAGE = Gauge(
    'skill_cpu_usage_percent',
    'CPU usage percentage of skill executions',
    ['skill_id', 'skill_name']
)

# 系统信息
SYSTEM_INFO = Info(
    'opencode_platform',
    'OpenCode Platform system information'
)

# 设置系统信息
SYSTEM_INFO.info({
    'version': '1.0.0',
    'service': 'skill-executor'
})


# ============= 技能调用监控类 =============

class SkillMetrics:
    """技能调用监控"""

    @staticmethod
    def record_invocation(
        skill_id: int,
        skill_name: str,
        status: str,
        execution_type: str = "api",
        duration_seconds: Optional[float] = None,
        error_type: Optional[str] = None,
        memory_bytes: Optional[int] = None,
        cpu_percent: Optional[float] = None
    ):
        """
        记录技能调用
        
        Args:
            skill_id: 技能ID
            skill_name: 技能名称
            status: 执行状态 (success/error/timeout)
            execution_type: 执行类型 (api/websocket/scheduled)
            duration_seconds: 执行时长（秒）
            error_type: 错误类型（如果有错误）
            memory_bytes: 内存使用（字节）
            cpu_percent: CPU使用百分比
        """
        try:
            # 转换为字符串标签
            skill_id_str = str(skill_id)
            skill_name_safe = skill_name.replace('"', '\\"')
            
            # 记录调用计数
            SKILL_INVOCATIONS_TOTAL.labels(
                skill_id=skill_id_str,
                skill_name=skill_name_safe,
                status=status,
                execution_type=execution_type
            ).inc()
            
            # 记录响应时间
            if duration_seconds is not None:
                SKILL_INVOCATION_DURATION.labels(
                    skill_id=skill_id_str,
                    skill_name=skill_name_safe,
                    execution_type=execution_type
                ).observe(duration_seconds)
            
            # 记录错误
            if status == "error" and error_type:
                SKILL_ERRORS_TOTAL.labels(
                    skill_id=skill_id_str,
                    skill_name=skill_name_safe,
                    error_type=error_type
                ).inc()
            
            # 记录资源使用
            if memory_bytes is not None:
                SKILL_MEMORY_USAGE.labels(
                    skill_id=skill_id_str,
                    skill_name=skill_name_safe
                ).set(memory_bytes)
            
            if cpu_percent is not None:
                SKILL_CPU_USAGE.labels(
                    skill_id=skill_id_str,
                    skill_name=skill_name_safe
                ).set(cpu_percent)
                
        except Exception as e:
            logger.error(f"Failed to record skill metrics: {e}")

    @staticmethod
    def start_execution(execution_type: str = "api"):
        """开始执行时增加活跃计数"""
        try:
            SKILL_ACTIVE_EXECUTIONS.labels(execution_type=execution_type).inc()
        except Exception as e:
            logger.error(f"Failed to increment active executions: {e}")

    @staticmethod
    def end_execution(execution_type: str = "api"):
        """结束执行时减少活跃计数"""
        try:
            SKILL_ACTIVE_EXECUTIONS.labels(execution_type=execution_type).dec()
        except Exception as e:
            logger.error(f"Failed to decrement active executions: {e}")


class SkillExecutionTimer:
    """技能执行计时器上下文管理器"""
    
    def __init__(
        self,
        skill_id: int,
        skill_name: str,
        execution_type: str = "api"
    ):
        self.skill_id = skill_id
        self.skill_name = skill_name
        self.execution_type = execution_type
        self.start_time = None
        self.status = "success"
        self.error_type = None
    
    def __enter__(self):
        self.start_time = time.time()
        SkillMetrics.start_execution(self.execution_type)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 计算执行时长
        duration = time.time() - self.start_time if self.start_time else 0
        
        # 设置状态
        if exc_type is not None:
            self.status = "error"
            self.error_type = exc_type.__name__
        
        # 记录指标
        SkillMetrics.record_invocation(
            skill_id=self.skill_id,
            skill_name=self.skill_name,
            status=self.status,
            execution_type=self.execution_type,
            duration_seconds=duration,
            error_type=self.error_type
        )
        
        # 结束执行
        SkillMetrics.end_execution(self.execution_type)
        
        # 不处理异常，让它继续传播
        return False
    
    def set_error(self, error_type: str):
        """设置错误类型"""
        self.status = "error"
        self.error_type = error_type
    
    def set_status(self, status: str):
        """设置执行状态"""
        self.status = status
