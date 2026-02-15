"""
计费数据模型

包含套餐、用量记录、账单、订阅等模型
"""
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, Boolean, DateTime, Text, JSON, Numeric, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class BillingPlanType(str, enum.Enum):
    """套餐类型"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class BillingCycle(str, enum.Enum):
    """计费周期"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class BillingUsageType(str, enum.Enum):
    """用量类型"""
    API_CALL = "api_call"  # API调用次数
    CPU_TIME = "cpu_time"  # CPU时间(秒)
    MEMORY = "memory"  # 内存使用(MB*秒)
    STORAGE = "storage"  # 存储使用(MB)
    EXECUTION_TIME = "execution_time"  # 执行时间(秒)


class SubscriptionStatus(str, enum.Enum):
    """订阅状态"""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"


class BillStatus(str, enum.Enum):
    """账单状态"""
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class BillingPlan(Base):
    """
    套餐模型
    
    定义不同的计费套餐
    """
    __tablename__ = "billing_plans"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # 套餐类型和周期
    plan_type: Mapped[BillingPlanType] = mapped_column(
        SQLEnum(BillingPlanType),
        default=BillingPlanType.BASIC,
        nullable=False
    )
    billing_cycle: Mapped[BillingCycle] = mapped_column(
        SQLEnum(BillingCycle),
        default=BillingCycle.MONTHLY,
        nullable=False
    )
    
    # 定价
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="CNY", nullable=False)
    
    # 配额限制
    api_call_limit: Mapped[int] = mapped_column(Integer, default=1000)  # API调用次数限制
    cpu_time_limit: Mapped[int] = mapped_column(Integer, default=3600)  # CPU时间限制(秒)
    memory_limit: Mapped[int] = mapped_column(Integer, default=1024)  # 内存限制(MB)
    storage_limit: Mapped[int] = mapped_column(Integer, default=1024)  # 存储限制(MB)
    execution_time_limit: Mapped[int] = mapped_column(Integer, default=3600)  # 执行时间限制(秒)
    
    # 超额计费单价
    overage_rate_api: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))  # 每次调用
    overage_rate_cpu: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))  # 每秒CPU
    overage_rate_memory: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))  # 每MB*秒
    overage_rate_storage: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))  # 每MB
    overage_rate_execution: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))  # 每秒执行
    
    # 功能特性
    features: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # 关系
    subscriptions = relationship("Subscription", back_populates="plan", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<BillingPlan(id={self.id}, name={self.name}, type={self.plan_type})>"


class Subscription(Base):
    """
    订阅模型
    
    用户订阅套餐的记录
    """
    __tablename__ = "subscriptions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("billing_plans.id", ondelete="RESTRICT"), nullable=False)
    
    # 订阅状态
    status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus),
        default=SubscriptionStatus.ACTIVE,
        nullable=False
    )
    
    # 时间范围
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # 当前周期用量（用于重置）
    current_period_start: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # 元数据
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # 关系
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("BillingPlan", back_populates="subscriptions")
    usage_records = relationship("BillingUsage", back_populates="subscription", cascade="all, delete-orphan")
    bills = relationship("BillingBill", back_populates="subscription", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user_id={self.user_id}, status={self.status})>"


class BillingUsage(Base):
    """
    用量记录模型
    
    记录用户使用资源的详细信息
    """
    __tablename__ = "billing_usage"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 技能信息
    skill_id: Mapped[Optional[int]] = mapped_column(ForeignKey("skills.id", ondelete="SET NULL"))
    skill_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # 用量类型
    usage_type: Mapped[BillingUsageType] = mapped_column(
        SQLEnum(BillingUsageType),
        nullable=False
    )
    
    # 用量数值
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0"), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="count")  # count, seconds, mb_seconds, mb
    
    # 费用计算
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal("0"), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal("0"), nullable=False)
    
    # 时间信息
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # 额外信息
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # 关系
    subscription = relationship("Subscription", back_populates="usage_records")
    user = relationship("User", back_populates="usage_records")
    skill = relationship("Skill", back_populates="usage_records")
    
    def __repr__(self) -> str:
        return f"<BillingUsage(id={self.id}, type={self.usage_type}, quantity={self.quantity})>"


class BillingBill(Base):
    """
    账单模型
    
    用户的账单记录
    """
    __tablename__ = "billing_bills"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subscription_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="SET NULL")
    )
    
    # 账单信息
    bill_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    
    # 时间范围
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # 金额明细
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    tax: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="CNY", nullable=False)
    
    # 账单状态
    status: Mapped[BillStatus] = mapped_column(
        SQLEnum(BillStatus),
        default=BillStatus.PENDING,
        nullable=False
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # 明细项目
    items: Mapped[Optional[List[dict]]] = mapped_column(JSON, default=list)
    
    # 备注
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # 关系
    user = relationship("User", back_populates="bills")
    subscription = relationship("Subscription", back_populates="bills")
    
    def __repr__(self) -> str:
        return f"<BillingBill(id={self.id}, bill_number={self.bill_number}, total={self.total_amount})>"
