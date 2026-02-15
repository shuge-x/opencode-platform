// 技能计费系统 Hooks

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getUsageStatistics,
  getUsageBySkill,
  getCostOverview,
  getCostTrend,
  getCallTrend,
  getResourceUsage,
  getSkillCategoryStats,
  getBills,
  getBillDetail,
  getPricingPlans,
  getPlanComparison,
  subscribePlan,
} from '@/api/billing'
import type {
  BillingQueryParams,
  BillQueryParams,
  SubscriptionRequest,
} from '@/types/billing'

// 用量统计
export function useUsageStatistics(params: BillingQueryParams) {
  return useQuery({
    queryKey: ['billing', 'usage-statistics', params],
    queryFn: () => getUsageStatistics(params),
  })
}

// 按技能分类的用量
export function useUsageBySkill(params: BillingQueryParams) {
  return useQuery({
    queryKey: ['billing', 'usage-by-skill', params],
    queryFn: () => getUsageBySkill(params),
  })
}

// 费用总览
export function useCostOverview() {
  return useQuery({
    queryKey: ['billing', 'cost-overview'],
    queryFn: getCostOverview,
  })
}

// 费用趋势
export function useCostTrend(params: BillingQueryParams) {
  return useQuery({
    queryKey: ['billing', 'cost-trend', params],
    queryFn: () => getCostTrend(params),
  })
}

// 调用趋势
export function useCallTrend(params: BillingQueryParams) {
  return useQuery({
    queryKey: ['billing', 'call-trend', params],
    queryFn: () => getCallTrend(params),
  })
}

// 资源使用
export function useResourceUsage(params: BillingQueryParams) {
  return useQuery({
    queryKey: ['billing', 'resource-usage', params],
    queryFn: () => getResourceUsage(params),
  })
}

// 技能分类统计
export function useSkillCategoryStats(params: BillingQueryParams) {
  return useQuery({
    queryKey: ['billing', 'skill-category-stats', params],
    queryFn: () => getSkillCategoryStats(params),
  })
}

// 账单列表
export function useBills(params: BillQueryParams) {
  return useQuery({
    queryKey: ['billing', 'bills', params],
    queryFn: () => getBills(params),
  })
}

// 账单详情
export function useBillDetail(billId: string) {
  return useQuery({
    queryKey: ['billing', 'bill', billId],
    queryFn: () => getBillDetail(billId),
    enabled: !!billId,
  })
}

// 套餐列表
export function usePricingPlans() {
  return useQuery({
    queryKey: ['billing', 'pricing-plans'],
    queryFn: getPricingPlans,
  })
}

// 套餐对比
export function usePlanComparison() {
  return useQuery({
    queryKey: ['billing', 'plan-comparison'],
    queryFn: getPlanComparison,
  })
}

// 订阅套餐
export function useSubscribePlan() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (request: SubscriptionRequest) => subscribePlan(request),
    onSuccess: () => {
      // 刷新相关数据
      queryClient.invalidateQueries({ queryKey: ['billing'] })
    },
  })
}
