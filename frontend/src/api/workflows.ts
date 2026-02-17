import axios from 'axios'
import type {
  Workflow,
  WorkflowExecution,
  CreateWorkflowRequest,
  UpdateWorkflowRequest,
} from '@/types/workflow'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 添加认证拦截器
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 工作流 CRUD API

/**
 * 获取工作流列表
 */
export async function getWorkflows(): Promise<Workflow[]> {
  const response = await api.get<Workflow[]>('/api/v1/workflows')
  return response.data
}

/**
 * 获取单个工作流
 */
export async function getWorkflow(id: string): Promise<Workflow> {
  const response = await api.get<Workflow>(`/api/v1/workflows/${id}`)
  return response.data
}

/**
 * 创建工作流
 */
export async function createWorkflow(data: CreateWorkflowRequest): Promise<Workflow> {
  const response = await api.post<Workflow>('/api/v1/workflows', data)
  return response.data
}

/**
 * 更新工作流
 */
export async function updateWorkflow(id: string, data: UpdateWorkflowRequest): Promise<Workflow> {
  const response = await api.put<Workflow>(`/api/v1/workflows/${id}`, data)
  return response.data
}

/**
 * 删除工作流
 */
export async function deleteWorkflow(id: string): Promise<void> {
  await api.delete(`/api/v1/workflows/${id}`)
}

// 工作流执行 API

/**
 * 执行工作流
 */
export async function executeWorkflow(
  id: string,
  input?: Record<string, unknown>
): Promise<WorkflowExecution> {
  const response = await api.post<WorkflowExecution>(
    `/api/v1/workflows/${id}/execute`,
    { input_data: input }
  )
  return response.data
}

/**
 * 获取工作流执行历史
 */
export async function getWorkflowExecutions(workflowId: string): Promise<WorkflowExecution[]> {
  const response = await api.get<WorkflowExecution[]>(
    `/api/v1/workflows/${workflowId}/executions`
  )
  return response.data
}

/**
 * 获取执行详情
 */
export async function getExecution(executionId: string): Promise<WorkflowExecution> {
  const response = await api.get<WorkflowExecution>(`/api/v1/executions/${executionId}`)
  return response.data
}

/**
 * 取消执行
 */
export async function cancelExecution(executionId: string): Promise<void> {
  await api.post(`/api/v1/executions/${executionId}/cancel`)
}

// Mock 数据（开发阶段使用）

export const mockWorkflows: Workflow[] = [
  {
    id: '1',
    name: '数据处理工作流',
    description: '自动处理数据并生成报告',
    user_id: 'user1',
    definition: {
      nodes: [
        {
          id: 'start-1',
          type: 'start',
          position: { x: 100, y: 100 },
          data: { type: 'start', label: '开始' },
        },
        {
          id: 'skill-1',
          type: 'skill',
          position: { x: 300, y: 100 },
          data: {
            type: 'skill',
            label: '数据获取',
            skillId: 'skill-123',
            skillName: '数据获取',
            inputMapping: {},
            outputMapping: { data: 'input_data' },
          },
        },
        {
          id: 'transform-1',
          type: 'transform',
          position: { x: 500, y: 100 },
          data: {
            type: 'transform',
            label: '数据转换',
            expressions: [
              {
                inputField: 'input_data',
                outputField: 'processed_data',
                transform: 'format',
              },
            ],
          },
        },
        {
          id: 'end-1',
          type: 'end',
          position: { x: 700, y: 100 },
          data: { type: 'end', label: '结束' },
        },
      ],
      edges: [
        { id: 'e1', source: 'start-1', target: 'skill-1' },
        { id: 'e2', source: 'skill-1', target: 'transform-1' },
        { id: 'e3', source: 'transform-1', target: 'end-1' },
      ],
    },
    variables: [
      {
        id: 'var-1',
        name: 'input_data',
        type: 'object',
        description: '输入数据',
        required: true,
      },
    ],
    is_active: true,
    created_at: '2024-02-15T10:00:00Z',
    updated_at: '2024-02-16T15:30:00Z',
  },
  {
    id: '2',
    name: '条件分支示例',
    description: '根据条件执行不同的分支',
    user_id: 'user1',
    definition: {
      nodes: [
        {
          id: 'start-2',
          type: 'start',
          position: { x: 100, y: 100 },
          data: { type: 'start', label: '开始' },
        },
        {
          id: 'condition-1',
          type: 'condition',
          position: { x: 300, y: 100 },
          data: {
            type: 'condition',
            label: '条件判断',
            conditions: {
              expressions: [
                { field: 'score', operator: 'greater_than', value: '80' },
              ],
              logic: 'and',
            },
          },
        },
        {
          id: 'skill-pass',
          type: 'skill',
          position: { x: 500, y: 50 },
          data: {
            type: 'skill',
            label: '高分处理',
            skillId: 'skill-456',
            skillName: '高分处理',
            inputMapping: {},
            outputMapping: {},
          },
        },
        {
          id: 'skill-fail',
          type: 'skill',
          position: { x: 500, y: 150 },
          data: {
            type: 'skill',
            label: '普通处理',
            skillId: 'skill-789',
            skillName: '普通处理',
            inputMapping: {},
            outputMapping: {},
          },
        },
        {
          id: 'end-2',
          type: 'end',
          position: { x: 700, y: 100 },
          data: { type: 'end', label: '结束' },
        },
      ],
      edges: [
        { id: 'e4', source: 'start-2', target: 'condition-1' },
        { id: 'e5', source: 'condition-1', target: 'skill-pass', sourceHandle: 'true' },
        { id: 'e6', source: 'condition-1', target: 'skill-fail', sourceHandle: 'false' },
        { id: 'e7', source: 'skill-pass', target: 'end-2' },
        { id: 'e8', source: 'skill-fail', target: 'end-2' },
      ],
    },
    variables: [
      {
        id: 'var-2',
        name: 'score',
        type: 'number',
        description: '分数',
        required: true,
      },
    ],
    is_active: true,
    created_at: '2024-02-14T08:00:00Z',
    updated_at: '2024-02-14T08:00:00Z',
  },
]

// 开发环境使用 mock 数据的包装函数
export async function getWorkflowsWithMock(): Promise<Workflow[]> {
  // 检查是否在开发环境且后端不可用
  if (import.meta.env.DEV) {
    try {
      return await getWorkflows()
    } catch {
      console.warn('Backend not available, using mock data')
      return mockWorkflows
    }
  }
  return getWorkflows()
}

export async function getWorkflowWithMock(id: string): Promise<Workflow> {
  if (import.meta.env.DEV) {
    try {
      return await getWorkflow(id)
    } catch {
      console.warn('Backend not available, using mock data')
      const workflow = mockWorkflows.find((w) => w.id === id)
      if (!workflow) throw new Error('Workflow not found')
      return workflow
    }
  }
  return getWorkflow(id)
}
