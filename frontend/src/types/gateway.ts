// API 网关路由规则
export interface RouteRule {
  id: string
  name: string
  description?: string
  path: string
  methods: HttpMethod[]
  target: string
  priority: number
  enabled: boolean
  rateLimitId?: string
  authRequired: boolean
  timeout: number
  retryCount: number
  createdAt: string
  updatedAt: string
}

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS'

export interface CreateRouteRequest {
  name: string
  description?: string
  path: string
  methods: HttpMethod[]
  target: string
  priority: number
  enabled: boolean
  rateLimitId?: string
  authRequired: boolean
  timeout: number
  retryCount: number
}

export interface UpdateRouteRequest extends Partial<CreateRouteRequest> {}

// 限流配置
export interface RateLimit {
  id: string
  name: string
  description?: string
  windowSize: number // 时间窗口（秒）
  maxRequests: number // 最大请求数
  strategy: RateLimitStrategy
  keyType: RateLimitKeyType
  enabled: boolean
  createdAt: string
  updatedAt: string
}

export type RateLimitStrategy = 'fixed_window' | 'sliding_window' | 'token_bucket' | 'leaky_bucket'
export type RateLimitKeyType = 'ip' | 'user' | 'api_key' | 'global'

export interface CreateRateLimitRequest {
  name: string
  description?: string
  windowSize: number
  maxRequests: number
  strategy: RateLimitStrategy
  keyType: RateLimitKeyType
  enabled: boolean
}

export interface UpdateRateLimitRequest extends Partial<CreateRateLimitRequest> {}

// API 密钥
export interface ApiKey {
  id: string
  name: string
  key: string
  description?: string
  scopes: string[]
  rateLimitId?: string
  expiresAt?: string
  lastUsedAt?: string
  usageCount: number
  enabled: boolean
  createdAt: string
  updatedAt: string
}

export interface CreateApiKeyRequest {
  name: string
  description?: string
  scopes: string[]
  rateLimitId?: string
  expiresAt?: string
}

export interface ApiKeyUsage {
  keyId: string
  date: string
  requestCount: number
  errorCount: number
  avgLatency: number
}

// 路由测试
export interface RouteTestRequest {
  path: string
  method: HttpMethod
  headers?: Record<string, string>
  body?: string
  queryParams?: Record<string, string>
}

export interface RouteTestResult {
  matched: boolean
  routeId?: string
  routeName?: string
  statusCode: number
  responseTime: number
  responseHeaders: Record<string, string>
  responseBody: string
  errors?: string[]
}

// 统计信息
export interface GatewayStats {
  totalRoutes: number
  activeRoutes: number
  totalRequests: number
  successRate: number
  avgLatency: number
  rateLimitedRequests: number
}

// 分页响应
export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
}
