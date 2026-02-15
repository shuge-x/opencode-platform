// 技能调用监控相关类型定义

export interface MonitoringOverview {
  totalCalls: number
  avgResponseTime: number
  errorRate: number
  throughput: number
  successRate: number
}

export interface CallTrendData {
  timestamp: string
  calls: number
  errors: number
  avgResponseTime: number
}

export interface ResponseTimeDistribution {
  range: string
  count: number
  percentage: number
}

export interface PerformanceMetrics {
  p50: number
  p95: number
  p99: number
  min: number
  max: number
  avg: number
}

export interface ResourceUsage {
  cpuUsage: number
  memoryUsage: number
  networkIn: number
  networkOut: number
  timestamp: string
}

export interface TopSkillRanking {
  id: string
  name: string
  calls: number
  avgResponseTime: number
  errorRate: number
  successRate: number
}

export interface ErrorRecord {
  id: string
  skillId: string
  skillName: string
  timestamp: string
  errorType: string
  errorMessage: string
  stackTrace?: string
  input?: string
  additionalInfo?: Record<string, unknown>
}

export interface MonitoringQueryParams {
  startDate?: string
  endDate?: string
  skillId?: string
  errorType?: string
  timeRange?: '1h' | '6h' | '24h' | '7d' | '30d'
  limit?: number
  offset?: number
}

export interface ErrorDetail extends ErrorRecord {
  requestDuration: number
  retryCount: number
  resolved: boolean
  resolvedAt?: string
  resolvedBy?: string
}
