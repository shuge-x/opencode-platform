// 计费系统 Mock 数据

import type {
  UsageStatistics,
  UsageBySkill,
  CostOverview,
  CostTrendData,
  CallTrendData,
  SkillCategoryStat,
  Bill,
  BillListResponse,
  PricingPlan,
  PlanComparison,
  ResourceUsageData,
} from '@/types/billing'

// 生成指定范围内的随机数
const randomInRange = (min: number, max: number) => 
  Math.floor(Math.random() * (max - min + 1)) + min

// 生成日期数组
const generateDates = (days: number): string[] => {
  const dates: string[] = []
  const now = new Date()
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    dates.push(date.toISOString().split('T')[0])
  }
  return dates
}

// 用量统计 Mock
export const mockUsageStatistics: UsageStatistics = {
  totalCalls: 15680,
  totalTokens: 2345000,
  totalCost: 234.56,
  totalDuration: 86400000,
  averageCostPerCall: 0.015,
  period: '30d',
}

// 按技能分类的用量统计
export const mockUsageBySkill: UsageBySkill[] = [
  {
    skillId: '1',
    skillName: '文本生成',
    calls: 5280,
    tokens: 1200000,
    cost: 120.0,
    avgResponseTime: 850,
    percentage: 33.7,
  },
  {
    skillId: '2',
    skillName: '代码助手',
    calls: 4150,
    tokens: 620000,
    cost: 62.0,
    avgResponseTime: 1200,
    percentage: 26.5,
  },
  {
    skillId: '3',
    skillName: '图像识别',
    calls: 3120,
    tokens: 310000,
    cost: 31.0,
    avgResponseTime: 650,
    percentage: 19.9,
  },
  {
    skillId: '4',
    skillName: '语音转文字',
    calls: 2080,
    tokens: 145000,
    cost: 14.56,
    avgResponseTime: 1800,
    percentage: 13.3,
  },
  {
    skillId: '5',
    skillName: '数据分析',
    calls: 1050,
    tokens: 70000,
    cost: 7.0,
    avgResponseTime: 2200,
    percentage: 6.7,
  },
]

// 费用总览 Mock
export const mockCostOverview: CostOverview = {
  currentBalance: 500.00,
  monthlySpend: 234.56,
  monthlyBudget: 500.00,
  projectedSpend: 280.00,
  budgetUsagePercent: 46.9,
}

// 费用趋势 Mock
export const mockCostTrendData: CostTrendData[] = generateDates(30).map(date => ({
  date,
  cost: randomInRange(5, 15) + Math.random(),
  calls: randomInRange(400, 700),
  tokens: randomInRange(50000, 100000),
}))

// 调用趋势 Mock
export const mockCallTrendData: CallTrendData[] = generateDates(30).map(date => ({
  timestamp: date,
  calls: randomInRange(400, 700),
  success: randomInRange(380, 680),
  errors: randomInRange(5, 30),
}))

// 资源使用 Mock
export const mockResourceUsageData: ResourceUsageData[] = generateDates(30).map(date => ({
  timestamp: date,
  cpuPercent: randomInRange(20, 80),
  memoryPercent: randomInRange(30, 70),
  networkIn: randomInRange(100, 500),
  networkOut: randomInRange(50, 300),
}))

// 技能分类统计 Mock
export const mockSkillCategoryStats: SkillCategoryStat[] = [
  { category: 'AI 对话', calls: 5280, cost: 120.0, percentage: 51.2 },
  { category: '代码开发', calls: 4150, cost: 62.0, percentage: 26.5 },
  { category: '媒体处理', calls: 3120, cost: 31.0, percentage: 13.2 },
  { category: '数据处理', calls: 3130, cost: 21.56, percentage: 9.2 },
]

// 账单 Mock
const generateBills = (): Bill[] => {
  const bills: Bill[] = []
  const statuses: Array<'pending' | 'paid' | 'overdue' | 'cancelled'> = ['paid', 'paid', 'paid', 'pending', 'paid']
  
  for (let i = 0; i < 12; i++) {
    const date = new Date()
    date.setMonth(date.getMonth() - i)
    const month = date.toISOString().slice(0, 7)
    const startDate = new Date(date.getFullYear(), date.getMonth(), 1)
    const endDate = new Date(date.getFullYear(), date.getMonth() + 1, 0)
    
    bills.push({
      id: `bill-${i + 1}`,
      billNo: `INV-${month.replace('-', '')}-${String(i + 1).padStart(4, '0')}`,
      period: month,
      startDate: startDate.toISOString(),
      endDate: endDate.toISOString(),
      totalAmount: randomInRange(150, 350) + Math.random(),
      status: statuses[i % statuses.length],
      createdAt: startDate.toISOString(),
      paidAt: i < 3 ? endDate.toISOString() : undefined,
      dueDate: new Date(startDate.getTime() + 15 * 24 * 60 * 60 * 1000).toISOString(),
      items: [
        {
          id: `item-${i}-1`,
          skillId: '1',
          skillName: '文本生成',
          calls: randomInRange(4000, 6000),
          tokens: randomInRange(800000, 1200000),
          unitPrice: 0.0001,
          amount: randomInRange(80, 120) + Math.random(),
        },
        {
          id: `item-${i}-2`,
          skillId: '2',
          skillName: '代码助手',
          calls: randomInRange(3000, 5000),
          tokens: randomInRange(400000, 700000),
          unitPrice: 0.0001,
          amount: randomInRange(40, 70) + Math.random(),
        },
      ],
    })
  }
  return bills
}

export const mockBills: Bill[] = generateBills()

// 账单列表响应 Mock
export const mockBillListResponse: BillListResponse = {
  data: mockBills.slice(0, 10),
  total: mockBills.length,
  page: 1,
  pageSize: 10,
}

// 套餐 Mock
export const mockPricingPlans: PricingPlan[] = [
  {
    id: 'free',
    name: 'free',
    displayName: '免费版',
    description: '适合个人用户和小型项目试用',
    price: 0,
    billingCycle: 'monthly',
    features: [
      { name: '每月调用次数', included: true, description: '1,000 次/月' },
      { name: '每月 Tokens', included: true, description: '100,000 tokens/月' },
      { name: '基础技能', included: true },
      { name: '社区支持', included: true },
      { name: '高级技能', included: false },
      { name: '优先支持', included: false },
      { name: 'SLA 保障', included: false },
      { name: 'API 高级功能', included: false },
    ],
    includedQuota: { calls: 1000, tokens: 100000 },
    overageRate: { callRate: 0.01, tokenRate: 0.0001 },
  },
  {
    id: 'pro',
    name: 'pro',
    displayName: '专业版',
    description: '适合成长型团队和商业项目',
    price: 99,
    billingCycle: 'monthly',
    recommended: true,
    features: [
      { name: '每月调用次数', included: true, description: '50,000 次/月' },
      { name: '每月 Tokens', included: true, description: '5,000,000 tokens/月' },
      { name: '基础技能', included: true },
      { name: '社区支持', included: true },
      { name: '高级技能', included: true },
      { name: '优先支持', included: true },
      { name: 'SLA 保障', included: false },
      { name: 'API 高级功能', included: false },
    ],
    includedQuota: { calls: 50000, tokens: 5000000 },
    overageRate: { callRate: 0.005, tokenRate: 0.00005 },
  },
  {
    id: 'enterprise',
    name: 'enterprise',
    displayName: '企业版',
    description: '适合大型企业和高并发场景',
    price: 499,
    billingCycle: 'monthly',
    features: [
      { name: '每月调用次数', included: true, description: '无限制' },
      { name: '每月 Tokens', included: true, description: '无限制' },
      { name: '基础技能', included: true },
      { name: '社区支持', included: true },
      { name: '高级技能', included: true },
      { name: '优先支持', included: true },
      { name: 'SLA 保障', included: true },
      { name: 'API 高级功能', included: true },
    ],
    includedQuota: { calls: -1, tokens: -1 }, // -1 表示无限制
    overageRate: { callRate: 0, tokenRate: 0 },
  },
]

// 套餐对比 Mock
export const mockPlanComparison: PlanComparison = {
  features: [
    '每月调用次数',
    '每月 Tokens',
    '基础技能',
    '高级技能',
    '社区支持',
    '优先支持',
    'SLA 保障',
    'API 高级功能',
  ],
  plans: [
    {
      id: 'free',
      name: '免费版',
      values: ['1,000 次', '100,000', true, false, true, false, false, false],
    },
    {
      id: 'pro',
      name: '专业版',
      values: ['50,000 次', '5,000,000', true, true, true, true, false, false],
    },
    {
      id: 'enterprise',
      name: '企业版',
      values: ['无限制', '无限制', true, true, true, true, true, true],
    },
  ],
}
