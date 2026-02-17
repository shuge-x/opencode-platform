import { create } from 'zustand'
import { Node, Edge, Connection } from '@xyflow/react'

export interface WorkflowNodeData {
  label: string
  type: 'start' | 'end' | 'skill'
  skillId?: string
  skillName?: string
  config?: Record<string, any>
}

export interface Workflow {
  id: string
  name: string
  description: string
  nodes: Node<WorkflowNodeData>[]
  edges: Edge[]
  variables: Variable[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Variable {
  name: string
  type: 'string' | 'number' | 'boolean' | 'object'
  defaultValue?: any
  description?: string
}

interface WorkflowState {
  // 当前工作流
  currentWorkflow: Workflow | null
  
  // 编辑器状态
  nodes: Node<WorkflowNodeData>[]
  edges: Edge[]
  selectedNode: string | null
  
  // 工作流列表
  workflows: Workflow[]
  
  // 变量
  variables: Variable[]
  
  // 执行状态
  isExecuting: boolean
  
  // Actions
  setCurrentWorkflow: (workflow: Workflow | null) => void
  setNodes: (nodes: Node<WorkflowNodeData>[]) => void
  setEdges: (edges: Edge[]) => void
  addNode: (node: Node<WorkflowNodeData>) => void
  updateNode: (nodeId: string, data: Partial<WorkflowNodeData>) => void
  removeNode: (nodeId: string) => void
  setSelectedNode: (nodeId: string | null) => void
  onConnect: (connection: Connection) => void
  setWorkflows: (workflows: Workflow[]) => void
  addVariable: (variable: Variable) => void
  removeVariable: (name: string) => void
  setIsExecuting: (isExecuting: boolean) => void
  reset: () => void
}

const initialState = {
  currentWorkflow: null,
  nodes: [],
  edges: [],
  selectedNode: null,
  workflows: [],
  variables: [],
  isExecuting: false,
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  ...initialState,

  setCurrentWorkflow: (workflow) => {
    set({
      currentWorkflow: workflow,
      nodes: workflow?.nodes || [],
      edges: workflow?.edges || [],
      variables: workflow?.variables || [],
    })
  },

  setNodes: (nodes) => set({ nodes }),
  
  setEdges: (edges) => set({ edges }),

  addNode: (node) => {
    set((state) => ({
      nodes: [...state.nodes, node],
    }))
  },

  updateNode: (nodeId, data) => {
    set((state) => ({
      nodes: state.nodes.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, ...data } }
          : node
      ),
    }))
  },

  removeNode: (nodeId) => {
    set((state) => ({
      nodes: state.nodes.filter((node) => node.id !== nodeId),
      edges: state.edges.filter(
        (edge) => edge.source !== nodeId && edge.target !== nodeId
      ),
      selectedNode: state.selectedNode === nodeId ? null : state.selectedNode,
    }))
  },

  setSelectedNode: (nodeId) => set({ selectedNode: nodeId }),

  onConnect: (connection) => {
    const { edges } = get()
    const newEdge: Edge = {
      id: `e${connection.source}-${connection.target}`,
      source: connection.source!,
      target: connection.target!,
      sourceHandle: connection.sourceHandle || undefined,
      targetHandle: connection.targetHandle || undefined,
    }
    set({ edges: [...edges, newEdge] })
  },

  setWorkflows: (workflows) => set({ workflows }),

  addVariable: (variable) => {
    set((state) => ({
      variables: [...state.variables, variable],
    }))
  },

  removeVariable: (name) => {
    set((state) => ({
      variables: state.variables.filter((v) => v.name !== name),
    }))
  },

  setIsExecuting: (isExecuting) => set({ isExecuting }),

  reset: () => set(initialState),
}))
