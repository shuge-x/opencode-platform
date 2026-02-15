"""
计费系统 API 路由

提供套餐管理、订阅、用量统计、账单等接口
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.security import get_current_user, get_current_admin_user
from app.models.user import User
from app.models.billing import (
    BillingPlan, Subscription, BillingUsage, BillingBill,
    BillingPlanType, BillingCycle, BillingUsageType, SubscriptionStatus, BillStatus
)
from app.schemas.billing import (
    # 套餐
    BillingPlanCreate, BillingPlanUpdate, BillingPlanResponse, BillingPlanListResponse,
    # 订阅
    SubscriptionCreate, SubscriptionResponse, SubscriptionListResponse,
    # 用量
    UsageQueryParams, UsageResponse, UsageSummary, UsageRecord, SkillUsageSummary,
    # 账单
    BillCreate, BillResponse, BillListResponse, BillGenerateResponse,
    # 配置
    BillingConfigResponse,
)
from app.services.usage_service import (
    UsageTrackingService,
    BillGenerationService,
    PlanService,
    SubscriptionService
)

router = APIRouter()


# ============ 套餐管理 ============

@router.get("/plans", response_model=BillingPlanListResponse)
async def list_plans(
    is_active: Optional[bool] = Query(None, description="是否激活"),
    is_public: Optional[bool] = Query(True, description="是否公开"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取套餐列表
    
    公开接口，获取所有可用的计费套餐
    """
    # 如果不是管理员，只显示公开的套餐
    plans, total = await PlanService.get_plans(
        db,
        is_active=is_active,
        is_public=is_public,
        page=page,
        page_size=page_size
    )
    
    return BillingPlanListResponse(
        items=[BillingPlanResponse.model_validate(p) for p in plans],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/plans", response_model=BillingPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_data: BillingPlanCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    创建新套餐
    
    管理员接口，创建新的计费套餐
    """
    # 检查 slug 是否已存在
    from sqlalchemy import select
    result = await db.execute(
        select(BillingPlan).where(BillingPlan.slug == plan_data.slug)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan with slug '{plan_data.slug}' already exists"
        )
    
    plan = await PlanService.create_plan(
        db,
        name=plan_data.name,
        slug=plan_data.slug,
        plan_type=plan_data.plan_type,
        billing_cycle=plan_data.billing_cycle,
        price=plan_data.price,
        description=plan_data.description,
        currency=plan_data.currency,
        api_call_limit=plan_data.api_call_limit,
        cpu_time_limit=plan_data.cpu_time_limit,
        memory_limit=plan_data.memory_limit,
        storage_limit=plan_data.storage_limit,
        execution_time_limit=plan_data.execution_time_limit,
        overage_rate_api=plan_data.overage_rate_api,
        overage_rate_cpu=plan_data.overage_rate_cpu,
        overage_rate_memory=plan_data.overage_rate_memory,
        overage_rate_storage=plan_data.overage_rate_storage,
        overage_rate_execution=plan_data.overage_rate_execution,
        features=plan_data.features,
        is_public=plan_data.is_public
    )
    
    return BillingPlanResponse.model_validate(plan)


@router.get("/plans/{plan_id}", response_model=BillingPlanResponse)
async def get_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取套餐详情
    """
    from sqlalchemy import select
    result = await db.execute(
        select(BillingPlan).where(BillingPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {plan_id} not found"
        )
    
    return BillingPlanResponse.model_validate(plan)


@router.put("/plans/{plan_id}", response_model=BillingPlanResponse)
async def update_plan(
    plan_id: int,
    plan_data: BillingPlanUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    更新套餐
    
    管理员接口，更新计费套餐信息
    """
    plan = await PlanService.update_plan(
        db,
        plan_id,
        **plan_data.model_dump(exclude_unset=True)
    )
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {plan_id} not found"
        )
    
    return BillingPlanResponse.model_validate(plan)


# ============ 订阅管理 ============

@router.post("/subscribe", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def subscribe_plan(
    subscription_data: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    订阅套餐
    
    用户订阅指定的计费套餐
    """
    try:
        subscription = await SubscriptionService.create_subscription(
            db,
            user_id=current_user.id,
            plan_id=subscription_data.plan_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return SubscriptionResponse.model_validate(subscription)


@router.get("/subscriptions", response_model=SubscriptionListResponse)
async def list_subscriptions(
    status: Optional[SubscriptionStatus] = Query(None, description="订阅状态"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户订阅列表
    """
    from sqlalchemy import select
    query = select(Subscription).where(Subscription.user_id == current_user.id)
    
    if status:
        query = query.where(Subscription.status == status)
    
    result = await db.execute(query)
    subscriptions = result.scalars().all()
    
    return SubscriptionListResponse(
        items=[SubscriptionResponse.model_validate(s) for s in subscriptions],
        total=len(subscriptions)
    )


@router.get("/subscriptions/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前活跃订阅
    """
    subscription = await SubscriptionService.get_user_subscription(
        db,
        user_id=current_user.id
    )
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    return SubscriptionResponse.model_validate(subscription)


@router.post("/subscriptions/{subscription_id}/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    取消订阅
    """
    subscription = await SubscriptionService.cancel_subscription(
        db,
        subscription_id=subscription_id,
        user_id=current_user.id
    )
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found"
        )
    
    return SubscriptionResponse.model_validate(subscription)


# ============ 用量统计 ============

@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    skill_id: Optional[int] = Query(None, description="技能ID"),
    usage_type: Optional[BillingUsageType] = Query(None, description="用量类型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取用量统计
    
    获取当前用户的资源使用情况，包括汇总和详细记录
    """
    # 默认查询当前周期
    if not start_date or not end_date:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
    
    # 获取用量汇总
    summaries = await UsageTrackingService.get_usage_summary(
        db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    # 获取按技能汇总
    skill_summaries = await UsageTrackingService.get_skill_usage_summary(
        db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    # 获取详细记录
    records, total = await UsageTrackingService.get_usage_records(
        db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        skill_id=skill_id,
        usage_type=usage_type,
        page=page,
        page_size=page_size
    )
    
    return UsageResponse(
        summaries=summaries,
        skill_summaries=skill_summaries,
        records=[UsageRecord.model_validate(r) for r in records],
        total_records=total,
        page=page,
        page_size=page_size,
        period_start=start_date,
        period_end=end_date
    )


@router.post("/usage/record")
async def record_usage(
    subscription_id: int,
    usage_type: BillingUsageType,
    quantity: float,
    skill_id: Optional[int] = None,
    skill_name: Optional[str] = None,
    metadata: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    记录用量
    
    内部接口，用于记录技能执行的资源使用（通常由系统调用）
    """
    from decimal import Decimal
    
    try:
        usage = await UsageTrackingService.record_usage(
            db,
            subscription_id=subscription_id,
            user_id=current_user.id,
            usage_type=usage_type,
            quantity=Decimal(str(quantity)),
            skill_id=skill_id,
            skill_name=skill_name,
            metadata=metadata
        )
        
        return {"message": "Usage recorded", "usage_id": usage.id}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============ 账单管理 ============

@router.get("/bills", response_model=BillListResponse)
async def list_bills(
    status: Optional[BillStatus] = Query(None, description="账单状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取账单列表
    
    获取当前用户的账单列表
    """
    bills, total = await BillGenerationService.get_bills(
        db,
        user_id=current_user.id,
        status=status,
        page=page,
        page_size=page_size
    )
    
    return BillListResponse(
        items=[BillResponse.model_validate(b) for b in bills],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/bills/{bill_id}", response_model=BillResponse)
async def get_bill(
    bill_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取账单详情
    """
    from sqlalchemy import select
    result = await db.execute(
        select(BillingBill).where(
            BillingBill.id == bill_id,
            BillingBill.user_id == current_user.id
        )
    )
    bill = result.scalar_one_or_none()
    
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill {bill_id} not found"
        )
    
    return BillResponse.model_validate(bill)


@router.post("/bills/generate", response_model=BillGenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate_bill(
    bill_data: BillCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    生成账单
    
    管理员接口，为指定用户生成账单
    """
    try:
        bill = await BillGenerationService.generate_bill(
            db,
            user_id=bill_data.user_id,
            period_start=bill_data.period_start,
            period_end=bill_data.period_end
        )
        
        return BillGenerateResponse(
            bill=BillResponse.model_validate(bill),
            message=f"Bill generated successfully: {bill.bill_number}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate bill: {str(e)}"
        )


@router.get("/config", response_model=BillingConfigResponse)
async def get_billing_config():
    """
    获取计费配置
    
    获取系统计费相关的配置信息
    """
    return BillingConfigResponse()
