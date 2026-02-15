import client from './client'
import type {
  RouteRule,
  CreateRouteRequest,
  UpdateRouteRequest,
  RateLimit,
  CreateRateLimitRequest,
  UpdateRateLimitRequest,
  ApiKey,
  CreateApiKeyRequest,
  ApiKeyUsage,
  RouteTestRequest,
  RouteTestResult,
  GatewayStats,
  PaginatedResponse,
  HttpMethod,
} from '@/types/gateway'

// 路由规则 API
export const routeApi = {
  // 获取路由列表
  list: async (params?: {
    page?: number
    pageSize?: number
    search?: string
    enabled?: boolean
  }): Promise<PaginatedResponse<RouteRule>> => {
    const response = await client.get('/gateway/routes', { params })
    return response.data
  },

  // 获取单个路由
  get: async (routeId: string): Promise<RouteRule> => {
    const response = await client.get(`/gateway/routes/${routeId}`)
    return response.data
  },

  // 创建路由
  create: async (request: CreateRouteRequest): Promise<RouteRule> => {
    const response = await client.post('/gateway/routes', request)
    return response.data
  },

  // 更新路由
  update: async (routeId: string, request: UpdateRouteRequest): Promise<RouteRule> => {
    const response = await client.put(`/gateway/routes/${routeId}`, request)
    return response.data
  },

  // 删除路由
  delete: async (routeId: string): Promise<void> => {
    await client.delete(`/gateway/routes/${routeId}`)
  },

  // 切换路由状态
  toggle: async (routeId: string, enabled: boolean): Promise<RouteRule> => {
    const response = await client.patch(`/gateway/routes/${routeId}/toggle`, { enabled })
    return response.data
  },

  // 测试路由
  test: async (request: RouteTestRequest): Promise<RouteTestResult> => {
    const response = await client.post('/gateway/routes/test', request)
    return response.data
  },

  // 批量更新优先级
  updatePriority: async (routes: { id: string; priority: number }[]): Promise<void> => {
    await client.put('/gateway/routes/priority', { routes })
  },
}

// 限流配置 API
export const rateLimitApi = {
  // 获取限流规则列表
  list: async (params?: {
    page?: number
    pageSize?: number
    search?: string
    enabled?: boolean
  }): Promise<PaginatedResponse<RateLimit>> => {
    const response = await client.get('/gateway/rate-limits', { params })
    return response.data
  },

  // 获取单个限流规则
  get: async (rateLimitId: string): Promise<RateLimit> => {
    const response = await client.get(`/gateway/rate-limits/${rateLimitId}`)
    return response.data
  },

  // 创建限流规则
  create: async (request: CreateRateLimitRequest): Promise<RateLimit> => {
    const response = await client.post('/gateway/rate-limits', request)
    return response.data
  },

  // 更新限流规则
  update: async (rateLimitId: string, request: UpdateRateLimitRequest): Promise<RateLimit> => {
    const response = await client.put(`/gateway/rate-limits/${rateLimitId}`, request)
    return response.data
  },

  // 删除限流规则
  delete: async (rateLimitId: string): Promise<void> => {
    await client.delete(`/gateway/rate-limits/${rateLimitId}`)
  },

  // 切换限流规则状态
  toggle: async (rateLimitId: string, enabled: boolean): Promise<RateLimit> => {
    const response = await client.patch(`/gateway/rate-limits/${rateLimitId}/toggle`, { enabled })
    return response.data
  },
}

// API 密钥 API
export const apiKeyApi = {
  // 获取密钥列表
  list: async (params?: {
    page?: number
    pageSize?: number
    search?: string
    enabled?: boolean
  }): Promise<PaginatedResponse<ApiKey>> => {
    const response = await client.get('/gateway/api-keys', { params })
    return response.data
  },

  // 获取单个密钥
  get: async (keyId: string): Promise<ApiKey> => {
    const response = await client.get(`/gateway/api-keys/${keyId}`)
    return response.data
  },

  // 创建密钥
  create: async (request: CreateApiKeyRequest): Promise<ApiKey> => {
    const response = await client.post('/gateway/api-keys', request)
    return response.data
  },

  // 删除密钥
  delete: async (keyId: string): Promise<void> => {
    await client.delete(`/gateway/api-keys/${keyId}`)
  },

  // 切换密钥状态
  toggle: async (keyId: string, enabled: boolean): Promise<ApiKey> => {
    const response = await client.patch(`/gateway/api-keys/${keyId}/toggle`, { enabled })
    return response.data
  },

  // 获取密钥使用统计
  getUsage: async (keyId: string, params?: {
    startDate?: string
    endDate?: string
  }): Promise<ApiKeyUsage[]> => {
    const response = await client.get(`/gateway/api-keys/${keyId}/usage`, { params })
    return response.data
  },

  // 重新生成密钥
  regenerate: async (keyId: string): Promise<ApiKey> => {
    const response = await client.post(`/gateway/api-keys/${keyId}/regenerate`)
    return response.data
  },
}

// 网关统计 API
export const gatewayStatsApi = {
  // 获取网关统计信息
  get: async (): Promise<GatewayStats> => {
    const response = await client.get('/gateway/stats')
    return response.data
  },
}
