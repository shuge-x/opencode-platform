import client from './client'
import type {
  MonitoringOverview,
  CallTrendData,
  ResponseTimeDistribution,
  PerformanceMetrics,
  ResourceUsage,
  TopSkillRanking,
  ErrorRecord,
  ErrorDetail,
  MonitoringQueryParams,
  PaginatedResponse,
} from '@/types/monitoring'

// Mock data imports (remove in production)
import {
  mockMonitoringOverview,
  mockCallTrendData,
  mockResponseTimeDistribution,
  mockPerformanceMetrics,
  mockResourceUsage,
  mockTopSkillRankings,
  mockErrors,
  mockErrorDetail,
} from './monitoring.mock'

// Flag to use mock data (set to false when backend is ready)
const USE_MOCK = true

// 获取监控总览数据
export const getMonitoringOverview = async (
  params?: MonitoringQueryParams
): Promise<MonitoringOverview> => {
  if (USE_MOCK) {
    return Promise.resolve(mockMonitoringOverview)
  }
  const response = await client.get<MonitoringOverview>('/monitoring/overview', { params })
  return response.data
}

// 获取调用趋势数据
export const getCallTrends = async (
  params?: MonitoringQueryParams
): Promise<CallTrendData[]> => {
  if (USE_MOCK) {
    return Promise.resolve(mockCallTrendData)
  }
  const response = await client.get<CallTrendData[]>('/monitoring/trends', { params })
  return response.data
}

// 获取响应时间分布
export const getResponseTimeDistribution = async (
  params?: MonitoringQueryParams
): Promise<ResponseTimeDistribution[]> => {
  if (USE_MOCK) {
    return Promise.resolve(mockResponseTimeDistribution)
  }
  const response = await client.get<ResponseTimeDistribution[]>('/monitoring/distribution', { params })
  return response.data
}

// 获取性能指标
export const getPerformanceMetrics = async (
  params?: MonitoringQueryParams
): Promise<PerformanceMetrics> => {
  if (USE_MOCK) {
    return Promise.resolve(mockPerformanceMetrics)
  }
  const response = await client.get<PerformanceMetrics>('/monitoring/performance', { params })
  return response.data
}

// 获取资源使用率
export const getResourceUsage = async (
  params?: MonitoringQueryParams
): Promise<ResourceUsage[]> => {
  if (USE_MOCK) {
    return Promise.resolve(mockResourceUsage)
  }
  const response = await client.get<ResourceUsage[]>('/monitoring/resources', { params })
  return response.data
}

// 获取 Top 技能排行
export const getTopSkillRankings = async (
  params?: MonitoringQueryParams
): Promise<TopSkillRanking[]> => {
  if (USE_MOCK) {
    return Promise.resolve(mockTopSkillRankings)
  }
  const response = await client.get<TopSkillRanking[]>('/monitoring/rankings', { params })
  return response.data
}

// 获取错误列表
export const getErrors = async (
  params?: MonitoringQueryParams
): Promise<PaginatedResponse<ErrorRecord>> => {
  if (USE_MOCK) {
    return Promise.resolve(mockErrors)
  }
  const response = await client.get<PaginatedResponse<ErrorRecord>>('/monitoring/errors', { params })
  return response.data
}

// 获取错误详情
export const getErrorDetail = async (errorId: string): Promise<ErrorDetail> => {
  if (USE_MOCK) {
    return Promise.resolve(mockErrorDetail as ErrorDetail)
  }
  const response = await client.get<ErrorDetail>(`/monitoring/errors/${errorId}`)
  return response.data
}

// 实时监控数据流（返回 WebSocket URL）
export const getRealtimeMonitoringUrl = (): string => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${wsProtocol}//${window.location.host}/api/monitoring/realtime`
}
