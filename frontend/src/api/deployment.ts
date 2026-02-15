import client from './client'
import type {
  Deployment,
  DeploymentConfig,
  CreateDeploymentRequest,
  UpdateDeploymentRequest,
  AddDomainRequest,
  DomainConfig,
  DeploymentLog,
} from '@/types/deployment'

export const deploymentApi = {
  // 获取所有部署
  listDeployments: async (): Promise<Deployment[]> => {
    const response = await client.get('/deployments')
    return response.data
  },

  // 获取单个部署详情
  getDeployment: async (deploymentId: string): Promise<Deployment> => {
    const response = await client.get(`/deployments/${deploymentId}`)
    return response.data
  },

  // 创建部署
  createDeployment: async (request: CreateDeploymentRequest): Promise<Deployment> => {
    const response = await client.post('/deployments', request)
    return response.data
  },

  // 更新部署配置
  updateDeployment: async (deploymentId: string, request: UpdateDeploymentRequest): Promise<Deployment> => {
    const response = await client.put(`/deployments/${deploymentId}`, request)
    return response.data
  },

  // 启动部署
  startDeployment: async (deploymentId: string): Promise<Deployment> => {
    const response = await client.post(`/deployments/${deploymentId}/start`)
    return response.data
  },

  // 停止部署
  stopDeployment: async (deploymentId: string): Promise<void> => {
    await client.post(`/deployments/${deploymentId}/stop`)
  },

  // 重启部署
  restartDeployment: async (deploymentId: string): Promise<Deployment> => {
    const response = await client.post(`/deployments/${deploymentId}/restart`)
    return response.data
  },

  // 删除部署
  deleteDeployment: async (deploymentId: string): Promise<void> => {
    await client.delete(`/deployments/${deploymentId}`)
  },

  // 获取部署日志
  getDeploymentLogs: async (
    deploymentId: string,
    params?: {
      level?: 'info' | 'warn' | 'error' | 'debug'
      search?: string
      limit?: number
      offset?: number
    }
  ): Promise<{ logs: DeploymentLog[]; total: number }> => {
    const response = await client.get(`/deployments/${deploymentId}/logs`, { params })
    return response.data
  },

  // 获取部署配置
  getDeploymentConfig: async (deploymentId: string): Promise<DeploymentConfig> => {
    const response = await client.get(`/deployments/${deploymentId}/config`)
    return response.data
  },

  // 域名管理
  addDomain: async (deploymentId: string, request: AddDomainRequest): Promise<DomainConfig> => {
    const response = await client.post(`/deployments/${deploymentId}/domains`, request)
    return response.data
  },

  removeDomain: async (deploymentId: string, domainId: string): Promise<void> => {
    await client.delete(`/deployments/${deploymentId}/domains/${domainId}`)
  },

  verifyDomain: async (deploymentId: string, domainId: string): Promise<DomainConfig> => {
    const response = await client.post(`/deployments/${deploymentId}/domains/${domainId}/verify`)
    return response.data
  },

  // 获取技能可部署版本
  getSkillVersions: async (skillId: string): Promise<string[]> => {
    const response = await client.get(`/skills/${skillId}/versions`)
    return response.data
  },

  // 下载日志
  downloadLogs: async (deploymentId: string): Promise<Blob> => {
    const response = await client.get(`/deployments/${deploymentId}/logs/download`, {
      responseType: 'blob'
    })
    return response.data
  },
}

// WebSocket 连接管理
export class DeploymentLogStream {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  constructor(
    private deploymentId: string,
    private onMessage: (log: DeploymentLog) => void,
    private onStatusChange?: (status: string) => void,
    private onError?: (error: Error) => void
  ) {}

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/deployments/${this.deploymentId}/logs/stream`
    
    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'log') {
          this.onMessage(data.payload)
        } else if (data.type === 'status') {
          this.onStatusChange?.(data.payload.status)
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      this.onError?.(new Error('WebSocket connection error'))
    }

    this.ws.onclose = () => {
      console.log('WebSocket closed')
      this.attemptReconnect()
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
      console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`)
      setTimeout(() => this.connect(), delay)
    }
  }

  disconnect() {
    this.reconnectAttempts = this.maxReconnectAttempts // Prevent reconnection
    this.ws?.close()
    this.ws = null
  }

  isConnected() {
    return this.ws?.readyState === WebSocket.OPEN
  }
}
