"""
技能监控服务

实现：
- 调用日志记录
- 日志查询
- 性能统计
- 错误追踪
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.sql import text
import json

from app.models.skill_invocation_log import SkillInvocationLog, SkillErrorLog
from app.core.skill_metrics import SkillMetrics
from app.core.cache import cache

logger = logging.getLogger(__name__)


class SkillMonitoringService:
    """技能监控服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============= 调用日志记录 =============

    async def record_invocation(
        self,
        skill_id: int,
        skill_name: str,
        status: str,
        execution_type: str = "api",
        skill_version: Optional[str] = None,
        user_id: Optional[int] = None,
        session_id: Optional[int] = None,
        request_id: Optional[str] = None,
        input_params: Optional[Dict[str, Any]] = None,
        output_data: Optional[str] = None,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        error_stack_trace: Optional[str] = None,
        duration_ms: Optional[int] = None,
        memory_bytes: Optional[int] = None,
        cpu_percent: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None
    ) -> SkillInvocationLog:
        """
        记录技能调用日志
        
        Args:
            skill_id: 技能ID
            skill_name: 技能名称
            status: 执行状态
            execution_type: 执行类型
            skill_version: 技能版本
            user_id: 用户ID
            session_id: 会话ID
            request_id: 请求ID
            input_params: 输入参数
            output_data: 输出数据
            error_message: 错误消息
            error_type: 错误类型
            error_stack_trace: 错误堆栈
            duration_ms: 执行时长（毫秒）
            memory_bytes: 内存使用
            cpu_percent: CPU使用百分比
            metadata: 元数据
            started_at: 开始时间
            completed_at: 完成时间
        
        Returns:
            创建的日志记录
        """
        # 创建日志记录
        log = SkillInvocationLog(
            skill_id=skill_id,
            skill_name=skill_name,
            skill_version=skill_version,
            execution_type=execution_type,
            status=status,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            input_params=input_params,
            output_data=output_data,
            error_message=error_message,
            error_type=error_type,
            error_stack_trace=error_stack_trace,
            duration_ms=duration_ms,
            memory_bytes=memory_bytes,
            cpu_percent=cpu_percent,
            metadata=metadata,
            started_at=started_at or datetime.utcnow(),
            completed_at=completed_at or datetime.utcnow()
        )
        
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        
        # 记录 Prometheus 指标
        SkillMetrics.record_invocation(
            skill_id=skill_id,
            skill_name=skill_name,
            status=status,
            execution_type=execution_type,
            duration_seconds=duration_ms / 1000 if duration_ms else None,
            error_type=error_type,
            memory_bytes=memory_bytes,
            cpu_percent=cpu_percent
        )
        
        # 如果有错误，记录错误日志
        if status == "error" and error_type:
            await self._record_error(
                skill_id=skill_id,
                skill_name=skill_name,
                error_type=error_type,
                error_message=error_message,
                error_stack_trace=error_stack_trace
            )
        
        # 更新 Redis 实时统计
        await self._update_realtime_stats(
            skill_id=skill_id,
            status=status,
            duration_ms=duration_ms
        )
        
        return log

    # ============= 日志查询 =============

    async def query_invocation_logs(
        self,
        skill_id: Optional[int] = None,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        execution_type: Optional[str] = None,
        error_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SkillInvocationLog]:
        """
        查询调用日志
        
        Args:
            skill_id: 技能ID
            user_id: 用户ID
            status: 执行状态
            execution_type: 执行类型
            error_type: 错误类型
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            日志列表
        """
        query = select(SkillInvocationLog)
        
        # 构建过滤条件
        conditions = []
        if skill_id is not None:
            conditions.append(SkillInvocationLog.skill_id == skill_id)
        if user_id is not None:
            conditions.append(SkillInvocationLog.user_id == user_id)
        if status:
            conditions.append(SkillInvocationLog.status == status)
        if execution_type:
            conditions.append(SkillInvocationLog.execution_type == execution_type)
        if error_type:
            conditions.append(SkillInvocationLog.error_type == error_type)
        if start_time:
            conditions.append(SkillInvocationLog.started_at >= start_time)
        if end_time:
            conditions.append(SkillInvocationLog.started_at <= end_time)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 排序和分页
        query = query.order_by(desc(SkillInvocationLog.started_at))
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_invocation_log(self, log_id: int) -> Optional[SkillInvocationLog]:
        """获取单条日志"""
        query = select(SkillInvocationLog).where(SkillInvocationLog.id == log_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ============= 性能统计 =============

    async def get_performance_stats(
        self,
        skill_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取性能统计
        
        Returns:
            性能统计数据
        """
        # 默认统计最近24小时
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.utcnow()
        
        # 构建基础查询
        base_conditions = [
            SkillInvocationLog.started_at >= start_time,
            SkillInvocationLog.started_at <= end_time
        ]
        if skill_id is not None:
            base_conditions.append(SkillInvocationLog.skill_id == skill_id)
        
        # 总体统计
        stats_query = select(
            func.count(SkillInvocationLog.id).label('total_invocations'),
            func.avg(SkillInvocationLog.duration_ms).label('avg_duration_ms'),
            func.min(SkillInvocationLog.duration_ms).label('min_duration_ms'),
            func.max(SkillInvocationLog.duration_ms).label('max_duration_ms'),
            func.sum(func.case((SkillInvocationLog.status == 'success', 1), else_=0)).label('success_count'),
            func.sum(func.case((SkillInvocationLog.status == 'error', 1), else_=0)).label('error_count'),
            func.sum(func.case((SkillInvocationLog.status == 'timeout', 1), else_=0)).label('timeout_count')
        ).where(and_(*base_conditions))
        
        stats_result = await self.db.execute(stats_query)
        stats_row = stats_result.one()
        
        total = stats_row.total_invocations or 0
        success_count = stats_row.success_count or 0
        error_count = stats_row.error_count or 0
        
        # 百分位数统计
        percentiles_query = select(
            func.percentile_cont(0.5).within_group(SkillInvocationLog.duration_ms).label('p50'),
            func.percentile_cont(0.95).within_group(SkillInvocationLog.duration_ms).label('p95'),
            func.percentile_cont(0.99).within_group(SkillInvocationLog.duration_ms).label('p99')
        ).where(and_(*base_conditions), SkillInvocationLog.duration_ms.isnot(None))
        
        percentiles_result = await self.db.execute(percentiles_query)
        percentiles_row = percentiles_result.one()
        
        return {
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "invocations": {
                "total": total,
                "success": success_count,
                "error": error_count,
                "timeout": stats_row.timeout_count or 0,
                "success_rate": round(success_count / total * 100, 2) if total > 0 else 0,
                "error_rate": round(error_count / total * 100, 2) if total > 0 else 0
            },
            "duration": {
                "avg_ms": round(stats_row.avg_duration_ms, 2) if stats_row.avg_duration_ms else None,
                "min_ms": stats_row.min_duration_ms,
                "max_ms": stats_row.max_duration_ms,
                "p50_ms": round(percentiles_row.p50, 2) if percentiles_row.p50 else None,
                "p95_ms": round(percentiles_row.p95, 2) if percentiles_row.p95 else None,
                "p99_ms": round(percentiles_row.p99, 2) if percentiles_row.p99 else None
            },
            "throughput": {
                "per_hour": round(total / max((end_time - start_time).total_seconds() / 3600, 1), 2),
                "per_minute": round(total / max((end_time - start_time).total_seconds() / 60, 1), 2)
            }
        }

    async def get_skill_rankings(
        self,
        metric: str = "invocations",  # invocations/errors/avg_duration
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取技能排行榜
        
        Args:
            metric: 排序指标
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量
        
        Returns:
            排行榜列表
        """
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.utcnow()
        
        # 根据指标选择排序字段
        if metric == "invocations":
            order_field = func.count(SkillInvocationLog.id).desc()
        elif metric == "errors":
            order_field = func.sum(
                func.case((SkillInvocationLog.status == 'error', 1), else_=0)
            ).desc()
        elif metric == "avg_duration":
            order_field = func.avg(SkillInvocationLog.duration_ms).desc()
        else:
            order_field = func.count(SkillInvocationLog.id).desc()
        
        query = select(
            SkillInvocationLog.skill_id,
            SkillInvocationLog.skill_name,
            func.count(SkillInvocationLog.id).label('total_invocations'),
            func.avg(SkillInvocationLog.duration_ms).label('avg_duration_ms'),
            func.sum(func.case((SkillInvocationLog.status == 'success', 1), else_=0)).label('success_count'),
            func.sum(func.case((SkillInvocationLog.status == 'error', 1), else_=0)).label('error_count')
        ).where(
            and_(
                SkillInvocationLog.started_at >= start_time,
                SkillInvocationLog.started_at <= end_time
            )
        ).group_by(
            SkillInvocationLog.skill_id,
            SkillInvocationLog.skill_name
        ).order_by(order_field).limit(limit)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        rankings = []
        for row in rows:
            total = row.total_invocations or 0
            error_count = row.error_count or 0
            rankings.append({
                "skill_id": row.skill_id,
                "skill_name": row.skill_name,
                "total_invocations": total,
                "avg_duration_ms": round(row.avg_duration_ms, 2) if row.avg_duration_ms else None,
                "success_count": row.success_count or 0,
                "error_count": error_count,
                "error_rate": round(error_count / total * 100, 2) if total > 0 else 0
            })
        
        return rankings

    # ============= 错误追踪 =============

    async def _record_error(
        self,
        skill_id: int,
        skill_name: str,
        error_type: str,
        error_message: Optional[str] = None,
        error_stack_trace: Optional[str] = None
    ):
        """记录错误到错误聚合表"""
        now = datetime.utcnow()
        
        # 查找是否已存在相同错误
        query = select(SkillErrorLog).where(
            and_(
                SkillErrorLog.skill_id == skill_id,
                SkillErrorLog.error_type == error_type,
                SkillErrorLog.error_message == error_message
            )
        )
        result = await self.db.execute(query)
        existing_error = result.scalar_one_or_none()
        
        if existing_error:
            # 更新现有错误记录
            existing_error.occurrence_count += 1
            existing_error.last_occurred_at = now
            if error_stack_trace:
                existing_error.sample_stack_trace = error_stack_trace
        else:
            # 创建新的错误记录
            new_error = SkillErrorLog(
                skill_id=skill_id,
                skill_name=skill_name,
                error_type=error_type,
                error_message=error_message,
                sample_stack_trace=error_stack_trace,
                first_occurred_at=now,
                last_occurred_at=now
            )
            self.db.add(new_error)
        
        await self.db.commit()

    async def get_error_logs(
        self,
        skill_id: Optional[int] = None,
        error_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[SkillErrorLog]:
        """
        查询错误日志
        
        Args:
            skill_id: 技能ID
            error_type: 错误类型
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量
        
        Returns:
            错误日志列表
        """
        query = select(SkillErrorLog)
        
        conditions = []
        if skill_id is not None:
            conditions.append(SkillErrorLog.skill_id == skill_id)
        if error_type:
            conditions.append(SkillErrorLog.error_type == error_type)
        if start_time:
            conditions.append(SkillErrorLog.last_occurred_at >= start_time)
        if end_time:
            conditions.append(SkillErrorLog.last_occurred_at <= end_time)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(SkillErrorLog.occurrence_count))
        query = query.limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_error_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取错误摘要
        
        Returns:
            错误摘要统计
        """
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.utcnow()
        
        # 按错误类型分组统计
        query = select(
            SkillErrorLog.error_type,
            func.sum(SkillErrorLog.occurrence_count).label('total_count'),
            func.count(SkillErrorLog.id).label('unique_count')
        ).where(
            and_(
                SkillErrorLog.last_occurred_at >= start_time,
                SkillErrorLog.last_occurred_at <= end_time
            )
        ).group_by(SkillErrorLog.error_type).order_by(desc('total_count'))
        
        result = await self.db.execute(query)
        rows = result.all()
        
        by_type = []
        for row in rows:
            by_type.append({
                "error_type": row.error_type,
                "total_occurrences": row.total_count,
                "unique_errors": row.unique_count
            })
        
        # 按技能分组统计
        skill_query = select(
            SkillErrorLog.skill_id,
            SkillErrorLog.skill_name,
            func.sum(SkillErrorLog.occurrence_count).label('total_count'),
            func.count(SkillErrorLog.id).label('unique_count')
        ).where(
            and_(
                SkillErrorLog.last_occurred_at >= start_time,
                SkillErrorLog.last_occurred_at <= end_time
            )
        ).group_by(
            SkillErrorLog.skill_id,
            SkillErrorLog.skill_name
        ).order_by(desc('total_count')).limit(10)
        
        skill_result = await self.db.execute(skill_query)
        skill_rows = skill_result.all()
        
        by_skill = []
        for row in skill_rows:
            by_skill.append({
                "skill_id": row.skill_id,
                "skill_name": row.skill_name,
                "total_errors": row.total_count,
                "unique_errors": row.unique_count
            })
        
        return {
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "by_type": by_type,
            "by_skill": by_skill
        }

    # ============= Redis 实时统计 =============

    async def _update_realtime_stats(
        self,
        skill_id: int,
        status: str,
        duration_ms: Optional[int] = None
    ):
        """更新 Redis 实时统计"""
        if not cache._connected or not cache.client:
            return
        
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            hour = datetime.utcnow().strftime("%H")
            
            # 更新调用计数
            await cache.client.incr(f"monitor:skill:{skill_id}:{today}:invocations")
            await cache.client.incr(f"monitor:skill:{skill_id}:{today}:hour:{hour}:invocations")
            
            # 更新状态计数
            await cache.client.incr(f"monitor:skill:{skill_id}:{today}:{status}")
            
            # 更新响应时间统计（使用 Redis 的 HyperLogLog 或简单的 list）
            if duration_ms is not None:
                await cache.client.lpush(
                    f"monitor:skill:{skill_id}:{today}:durations",
                    duration_ms
                )
                # 只保留最近1000条
                await cache.client.ltrim(f"monitor:skill:{skill_id}:{today}:durations", 0, 999)
            
        except Exception as e:
            logger.error(f"Failed to update realtime stats in Redis: {e}")

    async def get_realtime_stats(self, skill_id: int) -> Dict[str, Any]:
        """获取技能实时统计"""
        if not cache._connected or not cache.client:
            return {"error": "Redis not connected"}
        
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            
            # 获取今日统计
            invocations = await cache.client.get(f"monitor:skill:{skill_id}:{today}:invocations")
            success_count = await cache.client.get(f"monitor:skill:{skill_id}:{today}:success")
            error_count = await cache.client.get(f"monitor:skill:{skill_id}:{today}:error")
            
            # 获取响应时间
            durations = await cache.client.lrange(
                f"monitor:skill:{skill_id}:{today}:durations",
                0, 99  # 最近100条
            )
            
            # 计算平均响应时间
            avg_duration = None
            if durations:
                total = sum(int(d) for d in durations)
                avg_duration = round(total / len(durations), 2)
            
            return {
                "skill_id": skill_id,
                "date": today,
                "invocations": int(invocations) if invocations else 0,
                "success_count": int(success_count) if success_count else 0,
                "error_count": int(error_count) if error_count else 0,
                "avg_duration_ms": avg_duration
            }
        except Exception as e:
            logger.error(f"Failed to get realtime stats: {e}")
            return {"error": str(e)}
