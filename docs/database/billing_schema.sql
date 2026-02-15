-- =====================================================
-- 计费系统数据库架构
-- Sprint 18: 后端技能计费系统 (MVP)
-- =====================================================

-- 枚举类型
CREATE TYPE billing_plan_type AS ENUM ('free', 'basic', 'pro', 'enterprise');
CREATE TYPE billing_cycle AS ENUM ('daily', 'weekly', 'monthly', 'yearly');
CREATE TYPE billing_usage_type AS ENUM ('api_call', 'cpu_time', 'memory', 'storage', 'execution_time');
CREATE TYPE subscription_status AS ENUM ('active', 'cancelled', 'expired', 'pending');
CREATE TYPE bill_status AS ENUM ('pending', 'paid', 'cancelled', 'overdue');

-- =====================================================
-- 套餐表
-- =====================================================
CREATE TABLE billing_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    
    -- 套餐类型和周期
    plan_type billing_plan_type NOT NULL DEFAULT 'basic',
    billing_cycle billing_cycle NOT NULL DEFAULT 'monthly',
    
    -- 定价
    price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL DEFAULT 'CNY',
    
    -- 配额限制
    api_call_limit INTEGER NOT NULL DEFAULT 1000,
    cpu_time_limit INTEGER NOT NULL DEFAULT 3600,
    memory_limit INTEGER NOT NULL DEFAULT 1024,
    storage_limit INTEGER NOT NULL DEFAULT 1024,
    execution_time_limit INTEGER NOT NULL DEFAULT 3600,
    
    -- 超额计费单价
    overage_rate_api DECIMAL(10, 4),
    overage_rate_cpu DECIMAL(10, 4),
    overage_rate_memory DECIMAL(10, 4),
    overage_rate_storage DECIMAL(10, 4),
    overage_rate_execution DECIMAL(10, 4),
    
    -- 功能特性
    features JSONB DEFAULT '{}',
    
    -- 状态
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_public BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX ix_billing_plans_slug ON billing_plans(slug);
CREATE INDEX ix_billing_plans_plan_type ON billing_plans(plan_type);
CREATE INDEX ix_billing_plans_is_active ON billing_plans(is_active);
CREATE INDEX ix_billing_plans_is_public ON billing_plans(is_public);

-- 触发器：自动更新 updated_at
CREATE OR REPLACE FUNCTION update_billing_plans_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_billing_plans_updated_at
    BEFORE UPDATE ON billing_plans
    FOR EACH ROW
    EXECUTE FUNCTION update_billing_plans_updated_at();

-- =====================================================
-- 订阅表
-- =====================================================
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id INTEGER NOT NULL REFERENCES billing_plans(id) ON DELETE RESTRICT,
    
    -- 订阅状态
    status subscription_status NOT NULL DEFAULT 'active',
    
    -- 时间范围
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    cancelled_at TIMESTAMP,
    
    -- 当前周期用量
    current_period_start TIMESTAMP NOT NULL DEFAULT NOW(),
    current_period_end TIMESTAMP NOT NULL,
    
    -- 元数据
    metadata JSONB DEFAULT '{}',
    
    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX ix_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX ix_subscriptions_plan_id ON subscriptions(plan_id);
CREATE INDEX ix_subscriptions_status ON subscriptions(status);
CREATE INDEX ix_subscriptions_expires_at ON subscriptions(expires_at);

-- 触发器：自动更新 updated_at
CREATE OR REPLACE FUNCTION update_subscriptions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_subscriptions_updated_at();

-- =====================================================
-- 用量记录表
-- =====================================================
CREATE TABLE billing_usage (
    id SERIAL PRIMARY KEY,
    subscription_id INTEGER NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 技能信息
    skill_id INTEGER REFERENCES skills(id) ON DELETE SET NULL,
    skill_name VARCHAR(255),
    
    -- 用量类型
    usage_type billing_usage_type NOT NULL,
    
    -- 用量数值
    quantity DECIMAL(12, 4) NOT NULL DEFAULT 0,
    unit VARCHAR(50) NOT NULL DEFAULT 'count',
    
    -- 费用计算
    unit_price DECIMAL(10, 4) NOT NULL DEFAULT 0,
    total_cost DECIMAL(10, 4) NOT NULL DEFAULT 0,
    
    -- 时间信息
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    
    -- 额外信息
    metadata JSONB DEFAULT '{}'
);

-- 索引
CREATE INDEX ix_billing_usage_subscription_id ON billing_usage(subscription_id);
CREATE INDEX ix_billing_usage_user_id ON billing_usage(user_id);
CREATE INDEX ix_billing_usage_skill_id ON billing_usage(skill_id);
CREATE INDEX ix_billing_usage_usage_type ON billing_usage(usage_type);
CREATE INDEX ix_billing_usage_recorded_at ON billing_usage(recorded_at);
CREATE INDEX ix_billing_usage_period ON billing_usage(period_start, period_end);

-- 复合索引用于统计查询
CREATE INDEX ix_billing_usage_user_type_period ON billing_usage(user_id, usage_type, period_start, period_end);

-- =====================================================
-- 账单表
-- =====================================================
CREATE TABLE billing_bills (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id INTEGER REFERENCES subscriptions(id) ON DELETE SET NULL,
    
    -- 账单信息
    bill_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- 时间范围
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    due_date TIMESTAMP,
    
    -- 金额明细
    subtotal DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    tax DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    discount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    total_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL DEFAULT 'CNY',
    
    -- 账单状态
    status bill_status NOT NULL DEFAULT 'pending',
    paid_at TIMESTAMP,
    
    -- 明细项目
    items JSONB DEFAULT '[]',
    
    -- 备注
    notes TEXT,
    
    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 索引
CREATE UNIQUE INDEX ix_billing_bills_bill_number ON billing_bills(bill_number);
CREATE INDEX ix_billing_bills_user_id ON billing_bills(user_id);
CREATE INDEX ix_billing_bills_subscription_id ON billing_bills(subscription_id);
CREATE INDEX ix_billing_bills_status ON billing_bills(status);
CREATE INDEX ix_billing_bills_period ON billing_bills(period_start, period_end);
CREATE INDEX ix_billing_bills_due_date ON billing_bills(due_date);

-- 触发器：自动更新 updated_at
CREATE OR REPLACE FUNCTION update_billing_bills_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_billing_bills_updated_at
    BEFORE UPDATE ON billing_bills
    FOR EACH ROW
    EXECUTE FUNCTION update_billing_bills_updated_at();

-- =====================================================
-- 初始数据：默认套餐
-- =====================================================

-- 免费套餐
INSERT INTO billing_plans (name, slug, description, plan_type, billing_cycle, price, currency,
    api_call_limit, cpu_time_limit, memory_limit, storage_limit, execution_time_limit,
    features, is_active, is_public)
VALUES (
    '免费版',
    'free',
    '适合个人用户和小型项目',
    'free',
    'monthly',
    0.00,
    'CNY',
    1000,
    3600,
    512,
    512,
    3600,
    '{"max_skills": 5, "max_sessions": 10, "support": "community"}',
    TRUE,
    TRUE
);

-- 基础版
INSERT INTO billing_plans (name, slug, description, plan_type, billing_cycle, price, currency,
    api_call_limit, cpu_time_limit, memory_limit, storage_limit, execution_time_limit,
    overage_rate_api, overage_rate_cpu, overage_rate_memory, overage_rate_storage, overage_rate_execution,
    features, is_active, is_public)
VALUES (
    '基础版',
    'basic',
    '适合小型团队和中等规模项目',
    'basic',
    'monthly',
    99.00,
    'CNY',
    10000,
    36000,
    2048,
    2048,
    36000,
    0.001,
    0.0001,
    0.00001,
    0.001,
    0.0001,
    '{"max_skills": 20, "max_sessions": 50, "support": "email"}',
    TRUE,
    TRUE
);

-- 专业版
INSERT INTO billing_plans (name, slug, description, plan_type, billing_cycle, price, currency,
    api_call_limit, cpu_time_limit, memory_limit, storage_limit, execution_time_limit,
    overage_rate_api, overage_rate_cpu, overage_rate_memory, overage_rate_storage, overage_rate_execution,
    features, is_active, is_public)
VALUES (
    '专业版',
    'pro',
    '适合成长型企业和高频使用场景',
    'pro',
    'monthly',
    299.00,
    'CNY',
    100000,
    360000,
    8192,
    8192,
    360000,
    0.0005,
    0.00005,
    0.000005,
    0.0005,
    0.00005,
    '{"max_skills": 100, "max_sessions": 200, "support": "priority", "analytics": true}',
    TRUE,
    TRUE
);

-- 企业版
INSERT INTO billing_plans (name, slug, description, plan_type, billing_cycle, price, currency,
    api_call_limit, cpu_time_limit, memory_limit, storage_limit, execution_time_limit,
    features, is_active, is_public)
VALUES (
    '企业版',
    'enterprise',
    '适合大型企业，提供无限配额',
    'enterprise',
    'monthly',
    999.00,
    'CNY',
    -1,  -- -1 表示无限制
    -1,
    -1,
    -1,
    -1,
    '{"max_skills": -1, "max_sessions": -1, "support": "dedicated", "analytics": true, "sso": true, "audit_log": true}',
    TRUE,
    TRUE
);

-- =====================================================
-- 注释
-- =====================================================
COMMENT ON TABLE billing_plans IS '计费套餐表';
COMMENT ON TABLE subscriptions IS '用户订阅表';
COMMENT ON TABLE billing_usage IS '用量记录表';
COMMENT ON TABLE billing_bills IS '账单表';
