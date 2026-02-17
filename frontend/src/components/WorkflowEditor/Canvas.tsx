import React, { useCallback, useRef, DragEvent } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  Connection,
  OnNodesChange,
  OnEdgesChange,
  applyNodeChanges,
  applyEdgeChanges,
  NodeTypes,
  ReactFlowInstance,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useWorkflowStore, WorkflowNodeData } from '@/stores/workflowStore'
import { Node, Edge } from '@xyflow/react'
import StartNode from './nodes/StartNode'
import EndNode from './nodes/EndNode'
import SkillNode from './nodes/SkillNode'

const nodeTypes: NodeTypes = {
  start: StartNode,
  end: EndNode,
  skill: SkillNode,
}

const Canvas: React.FC = () => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const [reactFlowInstance, setReactFlowInstance] = React.useState<ReactFlowInstance | null>(null)
  
  const {
    nodes,
    edges,
    setNodes,
    setEdges,
    addNode,
    setSelectedNode,
    selectedNode,
  } = useWorkflowStore()
  
  const onNodesChange: OnNodesChange = useCallback(
    (changes) => {
      setNodes(applyNodeChanges(changes, nodes) as Node<WorkflowNodeData>[])
    },
    [nodes, setNodes]
  )
  
  const onEdgesChange: OnEdgesChange = useCallback(
    (changes) => {
      setEdges(applyEdgeChanges(changes, edges))
    },
    [edges, setEdges]
  )
  
  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges(addEdge(connection, edges))
    },
    [edges, setEdges]
  )
  
  const onDragOver = useCallback((event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])
  
  const onDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault()
      
      const type = event.dataTransfer.getData('application/reactflow')
      
      if (!type || !reactFlowInstance) {
        return
      }
      
      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      })
      
      const newNode: Node<WorkflowNodeData> = {
        id: `${type}_${Date.now()}`,
        type,
        position,
        data: {
          label: type === 'start' ? '开始' : type === 'end' ? '结束' : '技能节点',
          type: type as 'start' | 'end' | 'skill',
        },
      }
      
      addNode(newNode)
    },
    [reactFlowInstance, addNode]
  )
  
  const onNodeClick = useCallback(
    (event: React.MouseEvent, node: Node) => {
      setSelectedNode(node.id)
    },
    [setSelectedNode]
  )
  
  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
  }, [setSelectedNode])
  
  return (
    <div ref={reactFlowWrapper} style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onInit={setReactFlowInstance}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        fitView
        snapToGrid
        snapGrid={[15, 15]}
        style={{ background: '#f5f5f5' }}
      >
        <Background color="#aaa" gap={16} />
        <Controls />
        <MiniMap
          nodeStrokeWidth={3}
          zoomable
          pannable
          style={{
            background: '#fff',
          }}
        />
      </ReactFlow>
    </div>
  )
}

export default Canvas
