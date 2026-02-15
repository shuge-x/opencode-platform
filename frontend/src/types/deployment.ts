// 部署相关类型定义

// 环境变量
export interface EnvironmentVariable {
  id: string
  key: string
  value: string
  isSecret: boolean
  description?: string
}

// 端口配置
export interface PortConfig {
  port: number
  protocol: 'tcp' | 'udp'
  name?: string
}

// 资源限制
export interface ResourceLimits {
  cpu: number // CPU 核心数 (0.1 - 4)
  memory: number // 内存 MB (64 - 8192)
  storage?: number // 存储 MB (可选)
}

// 域名配置
export interface DomainConfig {
  id: string
  domain: string
  isVerified: boolean
  sslEnabled: boolean
  sslProvider?: 'letsencrypt' | 'custom'
  sslCert?: string
  sslKey?: string
  createdAt: string
  verifiedAt?: string
}

// 部署配置
export interface DeploymentConfig {
  skillId: string
  skillName: string
  version: string
  environmentVariables: EnvironmentVariable[]
  ports: PortConfig[]
  resources: ResourceLimits
  domains: DomainConfig[]
  replicas: number
  autoScaling: boolean
  minReplicas: number
  maxReplicas: number
}

// 部署状态
export type DeploymentStatus = 
  | 'pending'
  | 'building'
  | 'deploying'
  | 'running'
  | 'stopped'
  | 'failed'
  | 'updating'

// 部署实例
export interface Deployment {
  id: string
  skillId: string
  skillName: string
  version: string
  status: DeploymentStatus
  config: DeploymentConfig
  url?: string
  internalUrl?: string
  createdAt: string
  updatedAt: string
  startedAt?: string
  stoppedAt?: string
  errorMessage?: string
}

// 部署日志
export interface DeploymentLog {
  id: string
  deploymentId: string
  timestamp: string
  level: 'info' | 'warn' | 'error' | 'debug'
  message: string
  source?: string
}

// WebSocket 消息
export interface WebSocketMessage {
  type: 'log' | 'status' | 'error'
  payload: any
}

// 部署 API 请求类型
export interface CreateDeploymentRequest {
  skillId: string
  version: string
  environmentVariables: EnvironmentVariable[]
  ports: PortConfig[]
  resources: ResourceLimits
  replicas?: number
  autoScaling?: boolean
  minReplicas?: number
  maxReplicas?: number
}

export interface UpdateDeploymentRequest {
  environmentVariables?: EnvironmentVariable[]
  ports?: PortConfig[]
  resources?: ResourceLimits
  replicas?: number
  autoScaling?: boolean
  minReplicas?: number
  maxReplicas?: number
}

export interface AddDomainRequest {
  domain: string
  sslEnabled?: boolean
  sslProvider?: 'letsencrypt' | 'custom'
  sslCert?: string
  sslKey?: string
}

// 环境变量模板
export interface EnvTemplate {
  id: string
  name: string
  description: string
  variables: Omit<EnvironmentVariable, 'id'>[]
}

// 预定义的环境变量模板
export const ENV_TEMPLATES: EnvTemplate[] = [
  {
    id: 'database',
    name: '数据库配置',
    description: '常用数据库连接变量',
    variables: [
      { key: 'DATABASE_URL', value: '', isSecret: true, description: '数据库连接字符串' },
      { key: 'DB_HOST', value: 'localhost', isSecret: false, description: '数据库主机' },
      { key: 'DB_PORT', value: '5432', isSecret: false, description: '数据库端口' },
      { key: 'DB_NAME', value: '', isSecret: false, description: '数据库名称' },
      { key: 'DB_USER', value: '', isSecret: false, description: '数据库用户' },
      { key: 'DB_PASSWORD', value: '', isSecret: true, description: '数据库密码' },
    ]
  },
  {
    id: 'api',
    name: 'API 密钥',
    description: '外部 API 密钥配置',
    variables: [
      { key: 'API_KEY', value: '', isSecret: true, description: 'API 密钥' },
      { key: 'API_SECRET', value: '', isSecret: true, description: 'API 密钥' },
      { key: 'API_ENDPOINT', value: '', isSecret: false, description: 'API 端点' },
    ]
  },
  {
    id: 'redis',
    name: 'Redis 缓存',
    description: 'Redis 连接配置',
    variables: [
      { key: 'REDIS_URL', value: 'redis://localhost:6379', isSecret: true, description: 'Redis 连接字符串' },
      { key: 'REDIS_HOST', value: 'localhost', isSecret: false, description: 'Redis 主机' },
      { key: 'REDIS_PORT', value: '6379', isSecret: false, description: 'Redis 端口' },
      { key: 'REDIS_PASSWORD', value: '', isSecret: true, description: 'Redis 密码' },
    ]
  },
  {
    id: 'jwt',
    name: 'JWT 认证',
    description: 'JWT 认证配置',
    variables: [
      { key: 'JWT_SECRET', value: '', isSecret: true, description: 'JWT 密钥' },
      { key: 'JWT_EXPIRES_IN', value: '7d', isSecret: false, description: '过期时间' },
    ]
  },
]
