import client from './client'

export interface ToolCallResponse {
  id: number
  session_id: number
  message_id?: number
  tool_name: string
  tool_description?: string
  parameters?: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'permission_required' | 'permission_denied'
  result?: string
  error_message?: string
  requires_permission: boolean
  permission_granted?: boolean
  permission_reason?: string
  started_at?: string
  completed_at?: string
  created_at: string
  execution_logs: ExecutionLogResponse[]
}

export interface ExecutionLogResponse {
  id: number
  tool_call_id: number
  log_level: string
  message: string
  metadata?: string
  created_at: string
}

export interface ToolCallListResponse {
  items: ToolCallResponse[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export const toolsApi = {
  // 获取工具调用列表
  list: async (params?: {
    session_id?: number
    status?: string
    page?: number
    page_size?: number
  }): Promise<ToolCallListResponse> => {
    const response = await client.get('/tools', { params })
    return response.data
  },

  // 获取工具调用详情
  get: async (toolCallId: number): Promise<ToolCallResponse> => {
    const response = await client.get(`/tools/${toolCallId}`)
    return response.data
  },

  // 执行工具调用
  execute: async (toolCallId: number): Promise<ToolCallResponse> => {
    const response = await client.post(`/tools/${toolCallId}/execute`)
    return response.data
  },

  // 权限确认
  grantPermission: async (
    toolCallId: number,
    granted: boolean,
    reason?: string
  ): Promise<ToolCallResponse> => {
    const response = await client.post(`/tools/${toolCallId}/permission`, {
      granted,
      reason
    })
    return response.data
  },

  // 获取执行日志
  getLogs: async (toolCallId: number): Promise<ExecutionLogResponse[]> => {
    const response = await client.get(`/tools/${toolCallId}/logs`)
    return response.data
  }
}
