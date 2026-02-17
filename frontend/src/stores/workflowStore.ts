import { create } from 'zustand'
import type { 
  Workflow, 
  WorkflowNode, 
  WorkflowEdge, 
  WorkflowVariable,
  CreateWorkflowRequest,
  UpdateWorkflowRequest
} from '@/types/workflow'

interface WorkflowState {
  // 当前工作流
  currentWorkflow: Workflow | null
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  variables: WorkflowVariable[]
  
  // UI 状态
  selectedNode: string | null
  isExecuting: boolean
  isDirty: boolean
  loading: boolean
  
  // Actions - 工作流管理
  setCurrentWorkflow: (workflow: Workflow | null) => void
  createNewWorkflow: () => void
  
  // Actions - 节点管理
  setNodes: (nodes: WorkflowNode[]) => void
  addNode: (node: WorkflowNode) => void
  updateNode: (nodeId: string, data: Partial<WorkflowNode['data']>) => void
  removeNode: (nodeId: string) => void
  
  // Actions - 连接管理
  setEdges: (edges: WorkflowEdge[]) => void
  addEdge: (edge: WorkflowEdge) => void
  removeEdge: (edgeId: string) => void
  
  // Actions - 变量管理
  setVariables: (variables: WorkflowVariable[]) => void
  addVariable: (variable: WorkflowVariable) => void
  updateVariable: (variableId: string, updates: Partial<WorkflowVariable>) => void
  removeVariable: (variableId: string) => void
  
  // Actions - UI 状态
  setSelectedNode: (nodeId: string | null) => void
  setIsExecuting: (isExecuting: boolean) => void
  setIsDirty: (isDirty: boolean) => void
  setLoading: (loading: boolean) => void
  
  // Actions - 保存
  getWorkflowDefinition: () => CreateWorkflowRequest
  loadWorkflowDefinition: (workflow: Workflow) => void
  reset: () => void
}

const generateId = () => `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

const initialState = {
  currentWorkflow: null,
  nodes: [],
  edges: [],
  variables: [],
  selectedNode: null,
  isExecuting: false,
  isDirty: false,
  loading: false,
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  ...initialState,

  // 工作流管理
  setCurrentWorkflow: (workflow) => {
    if (workflow) {
      set({
        currentWorkflow: workflow,
        nodes: workflow.definition.nodes,
        edges: workflow.definition.edges,
        variables: workflow.variables,
        isDirty: false,
      })
    } else {
      set(initialState)
    }
  },

  createNewWorkflow: () => {
    const startNodeId = generateId()
    const startNode: WorkflowNode = {
      id: startNodeId,
      type: 'start',
      position: { x: 250, y: 50 },
      data: {
        type: 'start',
        label: '开始',
        description: '工作流入口',
      },
    }

    const endNodeId = generateId()
    const endNode: WorkflowNode = {
      id: endNodeId,
      type: 'end',
      position: { x: 250, y: 400 },
      data: {
        type: 'end',
        label: '结束',
        description: '工作流出口',
      },
    }

    set({
      currentWorkflow: null,
      nodes: [startNode, endNode],
      edges: [],
      variables: [],
      selectedNode: null,
      isDirty: true,
    })
  },

  // 节点管理
  setNodes: (nodes) => set({ nodes, isDirty: true }),

  addNode: (node) => set((state) => ({
    nodes: [...state.nodes, node],
    isDirty: true,
  })),

  updateNode: (nodeId, data) => set((state) => ({
    nodes: state.nodes.map((node) =>
      node.id === nodeId ? { ...node, data: { ...node.data, ...data } } : node
    ),
    isDirty: true,
  })),

  removeNode: (nodeId) => set((state) => ({
    nodes: state.nodes.filter((node) => node.id !== nodeId),
    edges: state.edges.filter(
      (edge) => edge.source !== nodeId && edge.target !== nodeId
    ),
    selectedNode: state.selectedNode === nodeId ? null : state.selectedNode,
    isDirty: true,
  })),

  // 连接管理
  setEdges: (edges) => set({ edges, isDirty: true }),

  addEdge: (edge) => set((state) => ({
    edges: [...state.edges, edge],
    isDirty: true,
  })),

  removeEdge: (edgeId) => set((state) => ({
    edges: state.edges.filter((edge) => edge.id !== edgeId),
    isDirty: true,
  })),

  // 变量管理
  setVariables: (variables) => set({ variables, isDirty: true }),

  addVariable: (variable) => set((state) => ({
    variables: [...state.variables, variable],
    isDirty: true,
  })),

  updateVariable: (variableId, updates) => set((state) => ({
    variables: state.variables.map((v) =>
      v.id === variableId ? { ...v, ...updates } : v
    ),
    isDirty: true,
  })),

  removeVariable: (variableId) => set((state) => ({
    variables: state.variables.filter((v) => v.id !== variableId),
    isDirty: true,
  })),

  // UI 状态
  setSelectedNode: (nodeId) => set({ selectedNode: nodeId }),
  setIsExecuting: (isExecuting) => set({ isExecuting }),
  setIsDirty: (isDirty) => set({ isDirty }),
  setLoading: (loading) => set({ loading }),

  // 保存相关
  getWorkflowDefinition: () => {
    const state = get()
    return {
      name: state.currentWorkflow?.name || '未命名工作流',
      description: state.currentWorkflow?.description || '',
      definition: {
        nodes: state.nodes,
        edges: state.edges,
      },
      variables: state.variables,
    }
  },

  loadWorkflowDefinition: (workflow) => {
    set({
      currentWorkflow: workflow,
      nodes: workflow.definition.nodes,
      edges: workflow.definition.edges,
      variables: workflow.variables,
      isDirty: false,
    })
  },

  reset: () => set(initialState),
}))
