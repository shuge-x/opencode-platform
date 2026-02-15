import { useQuery } from '@tanstack/react-query'
import {
  getMonitoringOverview,
  getCallTrends,
  getResponseTimeDistribution,
  getPerformanceMetrics,
  getResourceUsage,
  getTopSkillRankings,
  getErrors,
  getErrorDetail,
} from '@/api/monitoring'
import type { MonitoringQueryParams } from '@/types/monitoring'

// 监控总览
export const useMonitoringOverview = (params?: MonitoringQueryParams) => {
  return useQuery({
    queryKey: ['monitoring', 'overview', params],
    queryFn: () => getMonitoringOverview(params),
    refetchInterval: 30000, // 每 30 秒刷新
  })
}

// 调用趋势
export const useCallTrends = (params?: MonitoringQueryParams) => {
  return useQuery({
    queryKey: ['monitoring', 'trends', params],
    queryFn: () => getCallTrends(params),
    refetchInterval: 60000, // 每分钟刷新
  })
}

// 响应时间分布
export const useResponseTimeDistribution = (params?: MonitoringQueryParams) => {
  return useQuery({
    queryKey: ['monitoring', 'distribution', params],
    queryFn: () => getResponseTimeDistribution(params),
    refetchInterval: 60000,
  })
}

// 性能指标
export const usePerformanceMetrics = (params?: MonitoringQueryParams) => {
  return useQuery({
    queryKey: ['monitoring', 'performance', params],
    queryFn: () => getPerformanceMetrics(params),
    refetchInterval: 30000,
  })
}

// 资源使用率
export const useResourceUsage = (params?: MonitoringQueryParams) => {
  return useQuery({
    queryKey: ['monitoring', 'resources', params],
    queryFn: () => getResourceUsage(params),
    refetchInterval: 10000, // 每 10 秒刷新
  })
}

// Top 技能排行
export const useTopSkillRankings = (params?: MonitoringQueryParams) => {
  return useQuery({
    queryKey: ['monitoring', 'rankings', params],
    queryFn: () => getTopSkillRankings(params),
    refetchInterval: 60000,
  })
}

// 错误列表
export const useErrors = (params?: MonitoringQueryParams) => {
  return useQuery({
    queryKey: ['monitoring', 'errors', params],
    queryFn: () => getErrors(params),
    refetchInterval: 30000,
  })
}

// 错误详情
export const useErrorDetail = (errorId: string) => {
  return useQuery({
    queryKey: ['monitoring', 'error', errorId],
    queryFn: () => getErrorDetail(errorId),
    enabled: !!errorId,
  })
}
