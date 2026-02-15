"""
计费服务模块

处理用量统计、费用计算、账单生成等业务逻辑
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.billing import (
    BillingPlan, Subscription, BillingUsage, BillingBill,
    BillingPlanType, BillingCycle, BillingUsageType, SubscriptionStatus, BillStatus
)
from app.schemas.billing import (
    UsageSummary, SkillUsageSummary, UsageRecord, BillItem
)


class UsageTrackingService:
    """用量统计服务"""
    
    @staticmethod
    async def record_usage(
        db: AsyncSession,
        subscription_id: int,
        user_id: int,
        usage_type: BillingUsageType,
        quantity: Decimal,
        skill_id: Optional[int] = None,
        skill_name: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> BillingUsage:
        """
        记录用量
        
        Args:
            db: 数据库会话
            subscription_id: 订阅ID
            user_id: 用户ID
            usage_type: 用量类型
            quantity: 用量数值
            skill_id: 技能ID
            skill_name: 技能名称
            metadata: 额外元数据
        
        Returns:
            BillingUsage: 用量记录
        """
        # 获取订阅信息
        result = await db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        # 计算单价
        unit_price = UsageTrackingService._get_unit_price(subscription.plan, usage_type)
        
        # 计算总费用
        total_cost = quantity * unit_price
        
        # 确定单位
        unit = UsageTrackingService._get_unit(usage_type)
        
        # 创建用量记录
        usage = BillingUsage(
            subscription_id=subscription_id,
            user_id=user_id,
            skill_id=skill_id,
            skill_name=skill_name,
            usage_type=usage_type,
            quantity=quantity,
            unit=unit,
            unit_price=unit_price,
            total_cost=total_cost,
            period_start=subscription.current_period_start,
            period_end=subscription.current_period_end,
            metadata=metadata or {}
        )
        
        db.add(usage)
        await db.flush()
        
        return usage
    
    @staticmethod
    def _get_unit_price(plan: BillingPlan, usage_type: BillingUsageType) -> Decimal:
        """获取用量单价"""
        price_map = {
            BillingUsageType.API_CALL: plan.overage_rate_api,
            BillingUsageType.CPU_TIME: plan.overage_rate_cpu,
            BillingUsageType.MEMORY: plan.overage_rate_memory,
            BillingUsageType.STORAGE: plan.overage_rate_storage,
            BillingUsageType.EXECUTION_TIME: plan.overage_rate_execution,
        }
        return price_map.get(usage_type) or Decimal("0")
    
    @staticmethod
    def _get_unit(usage_type: BillingUsageType) -> str:
        """获取用量单位"""
        unit_map = {
            BillingUsageType.API_CALL: "count",
            BillingUsageType.CPU_TIME: "seconds",
            BillingUsageType.MEMORY: "mb_seconds",
            BillingUsageType.STORAGE: "mb",
            BillingUsageType.EXECUTION_TIME: "seconds",
        }
        return unit_map.get(usage_type, "count")
    
    @staticmethod
    async def get_usage_summary(
        db: AsyncSession,
        user_id: int,
        subscription_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[UsageSummary]:
        """
        获取用量汇总
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            subscription_id: 订阅ID(可选)
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            List[UsageSummary]: 用量汇总列表
        """
        # 构建查询
        query = select(
            BillingUsage.usage_type,
            func.sum(BillingUsage.quantity).label('total_quantity'),
            func.sum(BillingUsage.total_cost).label('total_cost')
        ).where(
            BillingUsage.user_id == user_id
        )
        
        if subscription_id:
            query = query.where(BillingUsage.subscription_id == subscription_id)
        
        if start_date:
            query = query.where(BillingUsage.recorded_at >= start_date)
        
        if end_date:
            query = query.where(BillingUsage.recorded_at <= end_date)
        
        query = query.group_by(BillingUsage.usage_type)
        
        result = await db.execute(query)
        rows = result.all()
        
        # 获取订阅配额
        limits = await UsageTrackingService._get_subscription_limits(db, user_id, subscription_id)
        
        # 构建汇总
        summaries = []
        for row in rows:
            usage_type = row.usage_type
            total_quantity = row.total_quantity or Decimal("0")
            total_cost = row.total_cost or Decimal("0")
            limit = limits.get(usage_type, 0)
            
            usage_percentage = 0.0
            if limit > 0:
                usage_percentage = float(total_quantity) / limit * 100
            
            summaries.append(UsageSummary(
                usage_type=usage_type,
                total_quantity=total_quantity,
                total_cost=total_cost,
                limit=limit,
                usage_percentage=usage_percentage
            ))
        
        # 确保所有用量类型都有记录
        all_types = list(BillingUsageType)
        existing_types = {s.usage_type for s in summaries}
        for usage_type in all_types:
            if usage_type not in existing_types:
                limit = limits.get(usage_type, 0)
                summaries.append(UsageSummary(
                    usage_type=usage_type,
                    total_quantity=Decimal("0"),
                    total_cost=Decimal("0"),
                    limit=limit,
                    usage_percentage=0.0
                ))
        
        return summaries
    
    @staticmethod
    async def _get_subscription_limits(
        db: AsyncSession,
        user_id: int,
        subscription_id: Optional[int] = None
    ) -> Dict[BillingUsageType, int]:
        """获取订阅配额限制"""
        # 获取活跃订阅
        query = select(Subscription).options(
            selectinload(Subscription.plan)
        ).where(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        )
        
        if subscription_id:
            query = query.where(Subscription.id == subscription_id)
        
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()
        
        if not subscription or not subscription.plan:
            return {}
        
        plan = subscription.plan
        return {
            BillingUsageType.API_CALL: plan.api_call_limit,
            BillingUsageType.CPU_TIME: plan.cpu_time_limit,
            BillingUsageType.MEMORY: plan.memory_limit,
            BillingUsageType.STORAGE: plan.storage_limit,
            BillingUsageType.EXECUTION_TIME: plan.execution_time_limit,
        }
    
    @staticmethod
    async def get_skill_usage_summary(
        db: AsyncSession,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[SkillUsageSummary]:
        """
        获取按技能汇总的用量
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            List[SkillUsageSummary]: 按技能汇总的用量列表
        """
        # 构建查询
        query = select(
            BillingUsage.skill_id,
            BillingUsage.skill_name,
            BillingUsage.usage_type,
            func.sum(BillingUsage.quantity).label('quantity'),
            func.sum(BillingUsage.total_cost).label('cost')
        ).where(
            BillingUsage.user_id == user_id
        )
        
        if start_date:
            query = query.where(BillingUsage.recorded_at >= start_date)
        
        if end_date:
            query = query.where(BillingUsage.recorded_at <= end_date)
        
        query = query.group_by(
            BillingUsage.skill_id,
            BillingUsage.skill_name,
            BillingUsage.usage_type
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        # 聚合到技能维度
        skill_map: Dict[str, SkillUsageSummary] = {}
        
        for row in rows:
            skill_key = f"{row.skill_id or 'unknown'}_{row.skill_name or 'Unknown'}"
            
            if skill_key not in skill_map:
                skill_map[skill_key] = SkillUsageSummary(
                    skill_id=row.skill_id,
                    skill_name=row.skill_name or "Unknown",
                    api_calls=0,
                    cpu_time=Decimal("0"),
                    memory_usage=Decimal("0"),
                    storage_usage=Decimal("0"),
                    execution_time=Decimal("0"),
                    total_cost=Decimal("0")
                )
            
            skill_summary = skill_map[skill_key]
            quantity = row.quantity or Decimal("0")
            cost = row.cost or Decimal("0")
            
            if row.usage_type == BillingUsageType.API_CALL:
                skill_summary.api_calls += int(quantity)
            elif row.usage_type == BillingUsageType.CPU_TIME:
                skill_summary.cpu_time += quantity
            elif row.usage_type == BillingUsageType.MEMORY:
                skill_summary.memory_usage += quantity
            elif row.usage_type == BillingUsageType.STORAGE:
                skill_summary.storage_usage += quantity
            elif row.usage_type == BillingUsageType.EXECUTION_TIME:
                skill_summary.execution_time += quantity
            
            skill_summary.total_cost += cost
        
        return list(skill_map.values())
    
    @staticmethod
    async def get_usage_records(
        db: AsyncSession,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skill_id: Optional[int] = None,
        usage_type: Optional[BillingUsageType] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[BillingUsage], int]:
        """
        获取用量记录列表
        
        Returns:
            tuple: (记录列表, 总数)
        """
        # 构建查询
        query = select(BillingUsage).where(BillingUsage.user_id == user_id)
        
        if start_date:
            query = query.where(BillingUsage.recorded_at >= start_date)
        
        if end_date:
            query = query.where(BillingUsage.recorded_at <= end_date)
        
        if skill_id:
            query = query.where(BillingUsage.skill_id == skill_id)
        
        if usage_type:
            query = query.where(BillingUsage.usage_type == usage_type)
        
        # 排序
        query = query.order_by(BillingUsage.recorded_at.desc())
        
        # 计数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await db.execute(query)
        records = result.scalars().all()
        
        return list(records), total


class BillGenerationService:
    """账单生成服务"""
    
    @staticmethod
    async def generate_bill(
        db: AsyncSession,
        user_id: int,
        period_start: datetime,
        period_end: datetime,
        subscription_id: Optional[int] = None
    ) -> BillingBill:
        """
        生成账单
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            period_start: 账单周期开始
            period_end: 账单周期结束
            subscription_id: 订阅ID(可选)
        
        Returns:
            BillingBill: 账单
        """
        # 获取用户订阅
        if not subscription_id:
            result = await db.execute(
                select(Subscription).where(
                    and_(
                        Subscription.user_id == user_id,
                        Subscription.status == SubscriptionStatus.ACTIVE
                    )
                )
            )
            subscription = result.scalar_one_or_none()
            subscription_id = subscription.id if subscription else None
        
        # 获取用量汇总
        usage_summaries = await UsageTrackingService.get_usage_summary(
            db, user_id, subscription_id, period_start, period_end
        )
        
        # 计算费用明细
        items = []
        subtotal = Decimal("0.00")
        
        for summary in usage_summaries:
            if summary.total_quantity > 0:
                # 获取配额限制
                limits = await UsageTrackingService._get_subscription_limits(
                    db, user_id, subscription_id
                )
                limit = limits.get(summary.usage_type, 0)
                
                # 计算超额部分
                overage = max(Decimal("0"), summary.total_quantity - Decimal(str(limit)))
                
                if overage > 0:
                    # 获取超额单价
                    unit_price = summary.total_cost / summary.total_quantity if summary.total_quantity > 0 else Decimal("0")
                    
                    item = BillItem(
                        description=f"{summary.usage_type.value} usage (overage)",
                        usage_type=summary.usage_type,
                        quantity=overage,
                        unit_price=unit_price,
                        amount=summary.total_cost
                    )
                    items.append(item)
                    subtotal += summary.total_cost
        
        # 计算税额和折扣（MVP阶段先设为0）
        tax = Decimal("0.00")
        discount = Decimal("0.00")
        total_amount = subtotal + tax - discount
        
        # 生成账单号
        bill_number = await BillGenerationService._generate_bill_number(db, period_start)
        
        # 设置到期日期（30天后）
        due_date = period_end + timedelta(days=30)
        
        # 创建账单
        bill = BillingBill(
            user_id=user_id,
            subscription_id=subscription_id,
            bill_number=bill_number,
            period_start=period_start,
            period_end=period_end,
            due_date=due_date,
            subtotal=subtotal,
            tax=tax,
            discount=discount,
            total_amount=total_amount,
            currency="CNY",
            status=BillStatus.PENDING,
            items=[item.model_dump() for item in items]
        )
        
        db.add(bill)
        await db.flush()
        
        return bill
    
    @staticmethod
    async def _generate_bill_number(db: AsyncSession, date: datetime) -> str:
        """生成账单号"""
        # 格式: BILL-YYYYMMDD-XXXXX
        prefix = f"BILL-{date.strftime('%Y%m%d')}"
        
        # 获取当日最大序号
        result = await db.execute(
            select(func.max(BillingBill.bill_number)).where(
                BillingBill.bill_number.like(f"{prefix}%")
            )
        )
        max_number = result.scalar()
        
        if max_number:
            # 提取序号并加1
            try:
                seq = int(max_number.split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}-{seq:05d}"
    
    @staticmethod
    async def get_bills(
        db: AsyncSession,
        user_id: Optional[int] = None,
        status: Optional[BillStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[BillingBill], int]:
        """
        获取账单列表
        
        Returns:
            tuple: (账单列表, 总数)
        """
        query = select(BillingBill)
        
        if user_id:
            query = query.where(BillingBill.user_id == user_id)
        
        if status:
            query = query.where(BillingBill.status == status)
        
        # 排序
        query = query.order_by(BillingBill.created_at.desc())
        
        # 计数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await db.execute(query)
        bills = result.scalars().all()
        
        return list(bills), total


class PlanService:
    """套餐管理服务"""
    
    @staticmethod
    async def create_plan(
        db: AsyncSession,
        name: str,
        slug: str,
        plan_type: BillingPlanType,
        billing_cycle: BillingCycle,
        price: Decimal,
        **kwargs
    ) -> BillingPlan:
        """创建套餐"""
        plan = BillingPlan(
            name=name,
            slug=slug,
            plan_type=plan_type,
            billing_cycle=billing_cycle,
            price=price,
            **kwargs
        )
        db.add(plan)
        await db.flush()
        return plan
    
    @staticmethod
    async def get_plans(
        db: AsyncSession,
        is_active: Optional[bool] = None,
        is_public: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[BillingPlan], int]:
        """获取套餐列表"""
        query = select(BillingPlan)
        
        if is_active is not None:
            query = query.where(BillingPlan.is_active == is_active)
        
        if is_public is not None:
            query = query.where(BillingPlan.is_public == is_public)
        
        query = query.order_by(BillingPlan.price.asc())
        
        # 计数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await db.execute(query)
        plans = result.scalars().all()
        
        return list(plans), total
    
    @staticmethod
    async def update_plan(
        db: AsyncSession,
        plan_id: int,
        **kwargs
    ) -> Optional[BillingPlan]:
        """更新套餐"""
        result = await db.execute(
            select(BillingPlan).where(BillingPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            return None
        
        for key, value in kwargs.items():
            if hasattr(plan, key) and value is not None:
                setattr(plan, key, value)
        
        await db.flush()
        return plan


class SubscriptionService:
    """订阅管理服务"""
    
    @staticmethod
    async def create_subscription(
        db: AsyncSession,
        user_id: int,
        plan_id: int
    ) -> Subscription:
        """
        创建订阅
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            plan_id: 套餐ID
        
        Returns:
            Subscription: 订阅记录
        """
        # 获取套餐信息
        result = await db.execute(
            select(BillingPlan).where(BillingPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        
        # 计算订阅周期
        now = datetime.utcnow()
        
        cycle_duration = {
            BillingCycle.DAILY: timedelta(days=1),
            BillingCycle.WEEKLY: timedelta(weeks=1),
            BillingCycle.MONTHLY: timedelta(days=30),
            BillingCycle.YEARLY: timedelta(days=365),
        }
        
        duration = cycle_duration.get(plan.billing_cycle, timedelta(days=30))
        expires_at = now + duration
        
        # 检查是否已有活跃订阅
        existing_result = await db.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.status == SubscriptionStatus.ACTIVE
                )
            )
        )
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            # 取消现有订阅
            existing.status = SubscriptionStatus.CANCELLED
            existing.cancelled_at = now
        
        # 创建新订阅
        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            status=SubscriptionStatus.ACTIVE,
            started_at=now,
            expires_at=expires_at,
            current_period_start=now,
            current_period_end=expires_at
        )
        
        db.add(subscription)
        await db.flush()
        
        return subscription
    
    @staticmethod
    async def get_user_subscription(
        db: AsyncSession,
        user_id: int
    ) -> Optional[Subscription]:
        """获取用户当前活跃订阅"""
        result = await db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.status == SubscriptionStatus.ACTIVE
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def cancel_subscription(
        db: AsyncSession,
        subscription_id: int,
        user_id: int
    ) -> Optional[Subscription]:
        """取消订阅"""
        result = await db.execute(
            select(Subscription).where(
                and_(
                    Subscription.id == subscription_id,
                    Subscription.user_id == user_id
                )
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return None
        
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = datetime.utcnow()
        
        await db.flush()
        return subscription
