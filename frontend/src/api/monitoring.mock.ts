// Mock data for monitoring development

import type {
  MonitoringOverview,
  CallTrendData,
  ResponseTimeDistribution,
  PerformanceMetrics,
  ResourceUsage,
  TopSkillRanking,
  ErrorRecord,
  PaginatedResponse,
} from '@/types/monitoring'

export const mockMonitoringOverview: MonitoringOverview = {
  totalCalls: 125847,
  avgResponseTime: 245,
  errorRate: 2.3,
  throughput: 156,
  successRate: 97.7,
}

export const mockCallTrendData: CallTrendData[] = Array.from({ length: 24 }, (_, i) => ({
  timestamp: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
  calls: Math.floor(Math.random() * 5000) + 1000,
  errors: Math.floor(Math.random() * 100) + 10,
  avgResponseTime: Math.floor(Math.random() * 300) + 100,
}))

export const mockResponseTimeDistribution: ResponseTimeDistribution[] = [
  { range: '0-50ms', count: 15420, percentage: 35.2 },
  { range: '50-100ms', count: 12340, percentage: 28.2 },
  { range: '100-200ms', count: 8760, percentage: 20.0 },
  { range: '200-500ms', count: 5230, percentage: 12.0 },
  { range: '500-1000ms', count: 1890, percentage: 4.3 },
  { range: '1000ms+', count: 107, percentage: 0.3 },
]

export const mockPerformanceMetrics: PerformanceMetrics = {
  p50: 120,
  p95: 480,
  p99: 890,
  min: 15,
  max: 2450,
  avg: 245,
}

export const mockResourceUsage: ResourceUsage[] = Array.from({ length: 24 }, (_, i) => ({
  timestamp: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
  cpuUsage: Math.floor(Math.random() * 40) + 30,
  memoryUsage: Math.floor(Math.random() * 30) + 50,
  networkIn: Math.floor(Math.random() * 500) + 100,
  networkOut: Math.floor(Math.random() * 400) + 80,
}))

export const mockTopSkillRankings: TopSkillRanking[] = [
  {
    id: '1',
    name: '天气查询',
    calls: 25430,
    avgResponseTime: 180,
    errorRate: 1.2,
    successRate: 98.8,
  },
  {
    id: '2',
    name: '文档搜索',
    calls: 18920,
    avgResponseTime: 320,
    errorRate: 2.5,
    successRate: 97.5,
  },
  {
    id: '3',
    name: '代码生成',
    calls: 15680,
    avgResponseTime: 450,
    errorRate: 3.1,
    successRate: 96.9,
  },
  {
    id: '4',
    name: '翻译助手',
    calls: 12340,
    avgResponseTime: 210,
    errorRate: 0.8,
    successRate: 99.2,
  },
  {
    id: '5',
    name: '数据分析',
    calls: 9870,
    avgResponseTime: 520,
    errorRate: 4.2,
    successRate: 95.8,
  },
]

export const mockErrors: PaginatedResponse<ErrorRecord> = {
  data: [
    {
      id: 'err-001',
      skillId: 'skill-003',
      skillName: '代码生成',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      errorType: 'TimeoutError',
      errorMessage: 'Request timeout after 30000ms',
      stackTrace: `TimeoutError: Request timeout after 30000ms
    at Timeout._onTimeout (/app/node_modules/request/request.js:878:12)
    at listOnTimeout (internal/timers.js:557:17)
    at processTimers (internal/timers.js:500:7)`,
      input: '{"prompt": "Generate a React component"}',
    },
    {
      id: 'err-002',
      skillId: 'skill-005',
      skillName: '数据分析',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      errorType: 'ValidationError',
      errorMessage: 'Invalid input data format: expected array, got object',
      stackTrace: `ValidationError: Invalid input data format
    at validateInput (/app/src/validators/index.js:45:11)
    at processData (/app/src/handlers/analytics.js:23:5)`,
      input: '{"data": {"invalid": "format"}}',
    },
    {
      id: 'err-003',
      skillId: 'skill-002',
      skillName: '文档搜索',
      timestamp: new Date(Date.now() - 10800000).toISOString(),
      errorType: 'NetworkError',
      errorMessage: 'Failed to connect to search service',
      stackTrace: `NetworkError: Failed to connect to search service
    at Connection.connect (/app/node_modules/elasticsearch/src/client.js:234:15)`,
    },
  ],
  total: 127,
  page: 1,
  pageSize: 20,
  hasMore: true,
}

export const mockErrorDetail = {
  ...mockErrors.data[0],
  requestDuration: 30000,
  retryCount: 3,
  resolved: false,
}
