import { Node, Edge } from '@xyflow/react'

// 工作流变量
export interface WorkflowVariable {
  id: string
  name: string
  type: 'string' | 'number' | 'boolean' | 'object' | 'array'
  defaultValue?: unknown
  description?: string
  required: boolean
}

// 条件表达式
export interface ConditionExpression {
  field: string
  operator: 'equals' | 'not_equals' | 'contains' | 'greater_than' | 'less_than' | 'is_empty' | 'is_not_empty'
  value: string
}

// 条件配置
export interface ConditionConfig {
  expressions: ConditionExpression[]
  logic: 'and' | 'or'  // 多个条件之间的逻辑关系
}

// 变换表达式
export interface TransformExpression {
  inputField: string
  outputField: string
  transform: 'copy' | 'rename' | 'format' | 'calculate' | 'custom'
  customExpression?: string
}

// 基础节点数据
export interface BaseNodeData {
  label: string
  description?: string
}

// 开始节点
export interface StartNodeData extends BaseNodeData {
  type: 'start'
}

// 结束节点
export interface EndNodeData extends BaseNodeData {
  type: 'end'
}

// 技能节点
export interface SkillNodeData extends BaseNodeData {
  type: 'skill'
  skillId: string
  skillName: string
  inputMapping: Record<string, string>  // 参数名 -> 变量引用
  outputMapping: Record<string, string> // 输出名 -> 变量名
}

// 条件节点
export interface ConditionNodeData extends BaseNodeData {
  type: 'condition'
  conditions: ConditionConfig
  trueLabel?: string
  falseLabel?: string
}

// 数据变换节点
export interface TransformNodeData extends BaseNodeData {
  type: 'transform'
  expressions: TransformExpression[]
}

// 节点数据联合类型
export type WorkflowNodeData = 
  | StartNodeData 
  | EndNodeData 
  | SkillNodeData 
  | ConditionNodeData 
  | TransformNodeData

// 工作流节点类型
export type WorkflowNode = Node<WorkflowNodeData>

// 工作流边类型
export type WorkflowEdge = Edge & {
  sourceHandle?: string
  targetHandle?: string
  label?: string
}

// 工作流定义
export interface Workflow {
  id: string
  name: string
  description: string
  user_id: string
  definition: {
    nodes: WorkflowNode[]
    edges: WorkflowEdge[]
  }
  variables: WorkflowVariable[]
  is_active: boolean
  created_at: string
  updated_at: string
}

// 工作流创建请求
export interface CreateWorkflowRequest {
  name: string
  description: string
  definition: {
    nodes: WorkflowNode[]
    edges: WorkflowEdge[]
  }
  variables: WorkflowVariable[]
}

// 工作流更新请求
export interface UpdateWorkflowRequest extends Partial<CreateWorkflowRequest> {
  is_active?: boolean
}

// 工作流执行状态
export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

// 工作流执行记录
export interface WorkflowExecution {
  id: string
  workflow_id: string
  trigger_type: 'manual' | 'scheduled' | 'webhook'
  status: ExecutionStatus
  input_data: Record<string, unknown>
  output_data?: Record<string, unknown>
  started_at: string
  finished_at?: string
  error_message?: string
  steps: ExecutionStep[]
}

// 执行步骤
export interface ExecutionStep {
  id: string
  execution_id: string
  node_id: string
  node_type: string
  status: ExecutionStatus
  input_data: Record<string, unknown>
  output_data?: Record<string, unknown>
  started_at: string
  finished_at?: string
  error_message?: string
}
