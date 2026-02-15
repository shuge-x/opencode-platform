// 技能计费系统 API

import client from './client'
import type {
  UsageStatistics,
  UsageBySkill,
  CostOverview,
  CostTrendData,
  CallTrendData,
  SkillCategoryStat,
  Bill,
  BillListResponse,
  BillQueryParams,
  PricingPlan,
  PlanComparison,
  SubscriptionRequest,
  SubscriptionResult,
  BillingQueryParams,
  ResourceUsageData,
  ExportParams,
} from '@/types/billing'

// 开发模式使用 Mock 数据
const USE_MOCK = true

import {
  mockUsageStatistics,
  mockUsageBySkill,
  mockCostOverview,
  mockCostTrendData,
  mockCallTrendData,
  mockSkillCategoryStats,
  mockBills,
  mockBillListResponse,
  mockPricingPlans,
  mockPlanComparison,
  mockResourceUsageData,
} from './billing.mock'

// 模拟延迟
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

// 获取用量统计
export async function getUsageStatistics(params: BillingQueryParams): Promise<UsageStatistics> {
  if (USE_MOCK) {
    await delay(300)
    return { ...mockUsageStatistics, period: params.timeRange }
  }
  const response = await client.get('/billing/usage/statistics', { params })
  return response.data
}

// 获取按技能分类的用量统计
export async function getUsageBySkill(params: BillingQueryParams): Promise<UsageBySkill[]> {
  if (USE_MOCK) {
    await delay(300)
    return mockUsageBySkill
  }
  const response = await client.get('/billing/usage/by-skill', { params })
  return response.data
}

// 获取费用总览
export async function getCostOverview(): Promise<CostOverview> {
  if (USE_MOCK) {
    await delay(200)
    return mockCostOverview
  }
  const response = await client.get('/billing/cost/overview')
  return response.data
}

// 获取费用趋势
export async function getCostTrend(params: BillingQueryParams): Promise<CostTrendData[]> {
  if (USE_MOCK) {
    await delay(400)
    return mockCostTrendData
  }
  const response = await client.get('/billing/cost/trend', { params })
  return response.data
}

// 获取调用趋势
export async function getCallTrend(params: BillingQueryParams): Promise<CallTrendData[]> {
  if (USE_MOCK) {
    await delay(400)
    return mockCallTrendData
  }
  const response = await client.get('/billing/calls/trend', { params })
  return response.data
}

// 获取资源使用情况
export async function getResourceUsage(params: BillingQueryParams): Promise<ResourceUsageData[]> {
  if (USE_MOCK) {
    await delay(400)
    return mockResourceUsageData
  }
  const response = await client.get('/billing/resources/usage', { params })
  return response.data
}

// 获取技能分类统计
export async function getSkillCategoryStats(params: BillingQueryParams): Promise<SkillCategoryStat[]> {
  if (USE_MOCK) {
    await delay(300)
    return mockSkillCategoryStats
  }
  const response = await client.get('/billing/skills/category-stats', { params })
  return response.data
}

// 获取账单列表
export async function getBills(params: BillQueryParams): Promise<BillListResponse> {
  if (USE_MOCK) {
    await delay(500)
    let filtered = [...mockBills]
    
    // 状态筛选
    if (params.status) {
      filtered = filtered.filter(bill => bill.status === params.status)
    }
    
    // 日期筛选
    if (params.startDate) {
      filtered = filtered.filter(bill => bill.startDate >= params.startDate!)
    }
    if (params.endDate) {
      filtered = filtered.filter(bill => bill.endDate <= params.endDate!)
    }
    
    const page = params.page || 1
    const pageSize = params.pageSize || 10
    const start = (page - 1) * pageSize
    const end = start + pageSize
    
    return {
      data: filtered.slice(start, end),
      total: filtered.length,
      page,
      pageSize,
    }
  }
  const response = await client.get('/billing/bills', { params })
  return response.data
}

// 获取账单详情
export async function getBillDetail(billId: string): Promise<Bill> {
  if (USE_MOCK) {
    await delay(300)
    const bill = mockBills.find(b => b.id === billId)
    if (!bill) {
      throw new Error('账单不存在')
    }
    return bill
  }
  const response = await client.get(`/billing/bills/${billId}`)
  return response.data
}

// 获取套餐列表
export async function getPricingPlans(): Promise<PricingPlan[]> {
  if (USE_MOCK) {
    await delay(300)
    return mockPricingPlans
  }
  const response = await client.get('/billing/plans')
  return response.data
}

// 获取套餐对比
export async function getPlanComparison(): Promise<PlanComparison> {
  if (USE_MOCK) {
    await delay(200)
    return mockPlanComparison
  }
  const response = await client.get('/billing/plans/comparison')
  return response.data
}

// 订阅套餐（仅 UI，无实际支付）
export async function subscribePlan(request: SubscriptionRequest): Promise<SubscriptionResult> {
  if (USE_MOCK) {
    await delay(800)
    return {
      success: true,
      message: `已成功订阅 ${request.planId} 套餐（${request.billingCycle === 'monthly' ? '月付' : '年付'}）`,
      subscriptionId: `sub-${Date.now()}`,
    }
  }
  const response = await client.post('/billing/subscriptions', request)
  return response.data
}

// 导出账单
export async function exportBills(params: ExportParams): Promise<Blob> {
  if (USE_MOCK) {
    await delay(500)
    // 模拟导出 CSV
    const csvContent = '账单编号,周期,金额,状态,创建时间\n' +
      mockBills.slice(0, 10).map(b => 
        `${b.billNo},${b.period},${b.totalAmount.toFixed(2)},${b.status},${b.createdAt}`
      ).join('\n')
    return new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  }
  const response = await client.get('/billing/bills/export', { 
    params,
    responseType: 'blob'
  })
  return response.data
}

// 下载导出的账单
export function downloadExportedBill(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}
