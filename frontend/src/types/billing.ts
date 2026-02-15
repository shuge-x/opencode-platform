// 技能计费系统类型定义

// 用量统计相关
export interface UsageStatistics {
  totalCalls: number
  totalTokens: number
  totalCost: number
  totalDuration: number // 毫秒
  averageCostPerCall: number
  period: TimeRange
}

export interface UsageBySkill {
  skillId: string
  skillName: string
  calls: number
  tokens: number
  cost: number
  avgResponseTime: number
  percentage: number
}

export interface CostOverview {
  currentBalance: number
  monthlySpend: number
  monthlyBudget: number
  projectedSpend: number
  budgetUsagePercent: number
}

// 费用趋势数据
export interface CostTrendData {
  date: string
  cost: number
  calls: number
  tokens: number
}

// 资源使用数据
export interface ResourceUsageData {
  timestamp: string
  cpuPercent: number
  memoryPercent: number
  networkIn: number
  networkOut: number
}

// 调用趋势数据
export interface CallTrendData {
  timestamp: string
  calls: number
  success: number
  errors: number
}

// 技能分类统计
export interface SkillCategoryStat {
  category: string
  calls: number
  cost: number
  percentage: number
}

// 账单相关
export interface Bill {
  id: string
  billNo: string
  period: string // 例如 "2024-01"
  startDate: string
  endDate: string
  totalAmount: number
  status: BillStatus
  createdAt: string
  paidAt?: string
  dueDate: string
  items: BillItem[]
}

export interface BillItem {
  id: string
  skillId: string
  skillName: string
  calls: number
  tokens: number
  unitPrice: number
  amount: number
}

export type BillStatus = 'pending' | 'paid' | 'overdue' | 'cancelled'

// 账单查询参数
export interface BillQueryParams {
  startDate?: string
  endDate?: string
  status?: BillStatus
  page?: number
  pageSize?: number
}

// 账单列表响应
export interface BillListResponse {
  data: Bill[]
  total: number
  page: number
  pageSize: number
}

// 套餐相关
export interface PricingPlan {
  id: string
  name: string
  displayName: string
  description: string
  price: number
  billingCycle: 'monthly' | 'yearly'
  features: PlanFeature[]
  includedQuota: {
    calls: number
    tokens: number
  }
  overageRate: {
    callRate: number
    tokenRate: number
  }
  recommended?: boolean
}

export interface PlanFeature {
  name: string
  included: boolean
  description?: string
}

export interface PlanComparison {
  features: string[]
  plans: {
    id: string
    name: string
    values: (string | boolean | number)[]
  }[]
}

// 订阅请求（仅 UI，无实际支付）
export interface SubscriptionRequest {
  planId: string
  billingCycle: 'monthly' | 'yearly'
}

export interface SubscriptionResult {
  success: boolean
  message: string
  subscriptionId?: string
}

// 时间范围类型
export type TimeRange = '7d' | '30d' | '90d' | '1y' | 'custom'

// 计费查询参数
export interface BillingQueryParams {
  timeRange: TimeRange
  startDate?: string
  endDate?: string
  skillId?: string
}

// 技能调用明细
export interface SkillCallRecord {
  id: string
  skillId: string
  skillName: string
  timestamp: string
  duration: number
  tokens: number
  cost: number
  status: 'success' | 'error'
}

// 导出参数
export interface ExportParams {
  type: 'csv' | 'pdf'
  startDate?: string
  endDate?: string
  billId?: string
}
