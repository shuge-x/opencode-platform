import { useCallback, useMemo } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type Edge,
  BackgroundVariant,
  type NodeTypes,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import {
  StartNode,
  EndNode,
  SkillNode,
  ConditionNode,
  TransformNode,
} from './nodes'
import { useWorkflowStore } from '@/stores/workflowStore'
import type { WorkflowNode, WorkflowEdge } from '@/types/workflow'

// 注册节点类型
const nodeTypes: NodeTypes = {
  start: StartNode,
  end: EndNode,
  skill: SkillNode,
  condition: ConditionNode,
  transform: TransformNode,
}

interface CanvasProps {
  className?: string
}

export default function Canvas({ className }: CanvasProps) {
  const { nodes, edges, setNodes, setEdges, setSelectedNode } = useWorkflowStore()

  // 转换节点为 React Flow 格式
  const [localNodes, setLocalNodes, onNodesChange] = useNodesState(nodes)
  const [localEdges, setLocalEdges, onEdgesChange] = useEdgesState(edges)

  // 同步节点变化到 store
  const handleNodesChange = useCallback(
    (changes: Parameters<typeof onNodesChange>[0]) => {
      onNodesChange(changes)
      // 延迟同步到 store，避免频繁更新
      setTimeout(() => {
        setNodes(localNodes as WorkflowNode[])
      }, 0)
    },
    [onNodesChange, localNodes, setNodes]
  )

  // 同步边变化到 store
  const handleEdgesChange = useCallback(
    (changes: Parameters<typeof onEdgesChange>[0]) => {
      onEdgesChange(changes)
      setTimeout(() => {
        setEdges(localEdges as WorkflowEdge[])
      }, 0)
    },
    [onEdgesChange, localEdges, setEdges]
  )

  // 处理新连接
  const onConnect = useCallback(
    (params: Connection) => {
      const newEdge = {
        ...params,
        id: `edge-${Date.now()}`,
        animated: true,
      } as WorkflowEdge
      setLocalEdges((eds) => addEdge(newEdge, eds))
      setEdges([...localEdges, newEdge] as WorkflowEdge[])
    },
    [localEdges, setEdges, setLocalEdges]
  )

  // 选中节点
  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: { id: string }) => {
      setSelectedNode(node.id)
    },
    [setSelectedNode]
  )

  // 点击画布空白处取消选中
  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
  }, [setSelectedNode])

  // MiniMap 节点颜色
  const nodeColor = useMemo(() => {
    return (node: { type?: string }) => {
      switch (node.type) {
        case 'start':
          return '#52c41a'
        case 'end':
          return '#ff4d4f'
        case 'skill':
          return '#1890ff'
        case 'condition':
          return '#fa8c16'
        case 'transform':
          return '#722ed1'
        default:
          return '#d9d9d9'
      }
    }
  }, [])

  return (
    <div className={className} style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={localNodes}
        edges={localEdges}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        fitView
        snapToGrid
        snapGrid={[15, 15]}
        defaultEdgeOptions={{
          animated: true,
          style: { strokeWidth: 2, stroke: '#1890ff' },
        }}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
        <Controls />
        <MiniMap nodeColor={nodeColor} nodeStrokeWidth={3} zoomable pannable />
      </ReactFlow>
    </div>
  )
}
