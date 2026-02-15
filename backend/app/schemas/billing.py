"""
计费相关 Pydantic Schemas

用于 API 请求和响应的数据验证
"""
from datetime import datetime
from typing import Optional, List, Dict
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum


class BillingPlanType(str, Enum):
    """套餐类型"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class BillingCycle(str, Enum):
    """计费周期"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class BillingUsageType(str, Enum):
    """用量类型"""
    API_CALL = "api_call"
    CPU_TIME = "cpu_time"
    MEMORY = "memory"
    STORAGE = "storage"
    EXECUTION_TIME = "execution_time"


class SubscriptionStatus(str, Enum):
    """订阅状态"""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"


class BillStatus(str, Enum):
    """账单状态"""
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


# ============ 套餐相关 ============

class BillingPlanBase(BaseModel):
    """套餐基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="套餐名称")
    slug: str = Field(..., min_length=1, max_length=100, description="套餐标识")
    description: Optional[str] = Field(None, description="套餐描述")
    plan_type: BillingPlanType = Field(default=BillingPlanType.BASIC, description="套餐类型")
    billing_cycle: BillingCycle = Field(default=BillingCycle.MONTHLY, description="计费周期")
    price: Decimal = Field(default=Decimal("0.00"), ge=0, description="价格")
    currency: str = Field(default="CNY", max_length=3, description="货币")
    
    # 配额
    api_call_limit: int = Field(default=1000, ge=0, description="API调用限制")
    cpu_time_limit: int = Field(default=3600, ge=0, description="CPU时间限制(秒)")
    memory_limit: int = Field(default=1024, ge=0, description="内存限制(MB)")
    storage_limit: int = Field(default=1024, ge=0, description="存储限制(MB)")
    execution_time_limit: int = Field(default=3600, ge=0, description="执行时间限制(秒)")
    
    # 超额计费
    overage_rate_api: Optional[Decimal] = Field(None, ge=0, description="API超额单价")
    overage_rate_cpu: Optional[Decimal] = Field(None, ge=0, description="CPU超额单价")
    overage_rate_memory: Optional[Decimal] = Field(None, ge=0, description="内存超额单价")
    overage_rate_storage: Optional[Decimal] = Field(None, ge=0, description="存储超额单价")
    overage_rate_execution: Optional[Decimal] = Field(None, ge=0, description="执行时间超额单价")
    
    # 功能特性
    features: Optional[Dict] = Field(default=None, description="功能特性")
    is_public: bool = Field(default=True, description="是否公开")


class BillingPlanCreate(BillingPlanBase):
    """创建套餐请求"""
    pass


class BillingPlanUpdate(BaseModel):
    """更新套餐请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    api_call_limit: Optional[int] = Field(None, ge=0)
    cpu_time_limit: Optional[int] = Field(None, ge=0)
    memory_limit: Optional[int] = Field(None, ge=0)
    storage_limit: Optional[int] = Field(None, ge=0)
    execution_time_limit: Optional[int] = Field(None, ge=0)
    overage_rate_api: Optional[Decimal] = Field(None, ge=0)
    overage_rate_cpu: Optional[Decimal] = Field(None, ge=0)
    overage_rate_memory: Optional[Decimal] = Field(None, ge=0)
    overage_rate_storage: Optional[Decimal] = Field(None, ge=0)
    overage_rate_execution: Optional[Decimal] = Field(None, ge=0)
    features: Optional[Dict] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class BillingPlanResponse(BillingPlanBase):
    """套餐响应"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BillingPlanListResponse(BaseModel):
    """套餐列表响应"""
    items: List[BillingPlanResponse]
    total: int
    page: int
    page_size: int


# ============ 订阅相关 ============

class SubscriptionCreate(BaseModel):
    """创建订阅请求"""
    plan_id: int = Field(..., description="套餐ID")
    billing_cycle: Optional[BillingCycle] = Field(None, description="计费周期(覆盖套餐默认)")


class SubscriptionResponse(BaseModel):
    """订阅响应"""
    id: int
    user_id: int
    plan_id: int
    status: SubscriptionStatus
    started_at: datetime
    expires_at: datetime
    current_period_start: datetime
    current_period_end: datetime
    plan: Optional[BillingPlanResponse] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SubscriptionListResponse(BaseModel):
    """订阅列表响应"""
    items: List[SubscriptionResponse]
    total: int


# ============ 用量统计相关 ============

class UsageRecord(BaseModel):
    """用量记录"""
    id: int
    usage_type: BillingUsageType
    skill_name: Optional[str]
    quantity: Decimal
    unit: str
    unit_price: Decimal
    total_cost: Decimal
    recorded_at: datetime
    period_start: datetime
    period_end: datetime
    
    class Config:
        from_attributes = True


class UsageSummary(BaseModel):
    """用量汇总"""
    usage_type: BillingUsageType
    total_quantity: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")
    limit: int = 0
    usage_percentage: float = 0.0
    
    @validator('usage_percentage', pre=True, always=True)
    def calculate_percentage(cls, v, values):
        if 'limit' in values and values['limit'] > 0:
            return float(values.get('total_quantity', 0)) / values['limit'] * 100
        return 0.0


class SkillUsageSummary(BaseModel):
    """按技能汇总的用量"""
    skill_id: Optional[int]
    skill_name: str
    api_calls: int = 0
    cpu_time: Decimal = Decimal("0")
    memory_usage: Decimal = Decimal("0")
    storage_usage: Decimal = Decimal("0")
    execution_time: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")


class UsageQueryParams(BaseModel):
    """用量查询参数"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skill_id: Optional[int] = None
    usage_type: Optional[BillingUsageType] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class UsageResponse(BaseModel):
    """用量统计响应"""
    # 汇总信息
    summaries: List[UsageSummary]
    skill_summaries: List[SkillUsageSummary]
    
    # 详细记录
    records: List[UsageRecord]
    
    # 分页信息
    total_records: int
    page: int
    page_size: int
    
    # 查询范围
    period_start: datetime
    period_end: datetime


# ============ 账单相关 ============

class BillItem(BaseModel):
    """账单明细项"""
    description: str
    usage_type: Optional[BillingUsageType]
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal


class BillCreate(BaseModel):
    """生成账单请求"""
    user_id: int = Field(..., description="用户ID")
    period_start: datetime = Field(..., description="账单周期开始")
    period_end: datetime = Field(..., description="账单周期结束")


class BillResponse(BaseModel):
    """账单响应"""
    id: int
    user_id: int
    subscription_id: Optional[int]
    bill_number: str
    period_start: datetime
    period_end: datetime
    due_date: Optional[datetime]
    subtotal: Decimal
    tax: Decimal
    discount: Decimal
    total_amount: Decimal
    currency: str
    status: BillStatus
    items: Optional[List[BillItem]]
    notes: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BillListResponse(BaseModel):
    """账单列表响应"""
    items: List[BillResponse]
    total: int
    page: int
    page_size: int


class BillGenerateResponse(BaseModel):
    """账单生成响应"""
    bill: BillResponse
    message: str


# ============ 计费配置相关 ============

class BillingConfigResponse(BaseModel):
    """计费配置响应"""
    default_currency: str = "CNY"
    supported_currencies: List[str] = ["CNY", "USD"]
    tax_rate: Decimal = Decimal("0.00")
    grace_period_days: int = 7
