import { useCallback } from 'react'
import { Typography, Card, Space, Tooltip } from 'antd'
import {
  PlayCircleOutlined,
  StopOutlined,
  ThunderboltOutlined,
  BranchesOutlined,
  TransformOutlined,
} from '@ant-design/icons'
import { useWorkflowStore } from '@/stores/workflowStore'
import type { WorkflowNode } from '@/types/workflow'
import './NodePalette.css'

const { Text } = Typography

interface PaletteNode {
  type: WorkflowNode['type']
  label: string
  icon: React.ReactNode
  color: string
  description: string
}

const paletteNodes: PaletteNode[] = [
  {
    type: 'start',
    label: '开始',
    icon: <PlayCircleOutlined />,
    color: '#52c41a',
    description: '工作流的入口点',
  },
  {
    type: 'end',
    label: '结束',
    icon: <StopOutlined />,
    color: '#ff4d4f',
    description: '工作流的出口点',
  },
  {
    type: 'skill',
    label: '技能',
    icon: <ThunderboltOutlined />,
    color: '#1890ff',
    description: '调用已安装的技能',
  },
  {
    type: 'condition',
    label: '条件',
    icon: <BranchesOutlined />,
    color: '#fa8c16',
    description: '根据条件分支执行',
  },
  {
    type: 'transform',
    label: '数据转换',
    icon: <TransformOutlined />,
    color: '#722ed1',
    description: '转换数据格式',
  },
]

export default function NodePalette() {
  const { addNode } = useWorkflowStore()

  const onDragStart = useCallback(
    (event: React.DragEvent, nodeType: PaletteNode) => {
      event.dataTransfer.setData('application/reactflow', nodeType.type)
      event.dataTransfer.effectAllowed = 'move'
    },
    []
  )

  const onDoubleClick = useCallback(
    (nodeType: PaletteNode) => {
      // 双击添加节点到画布中心
      const id = `${nodeType.type}-${Date.now()}`
      const newNode: WorkflowNode = {
        id,
        type: nodeType.type,
        position: { x: 250, y: 200 },
        data: createDefaultNodeData(nodeType.type),
      }
      addNode(newNode)
    },
    [addNode]
  )

  return (
    <div className="node-palette">
      <div className="palette-header">
        <Text strong>节点类型</Text>
      </div>
      <Space direction="vertical" className="palette-content">
        {paletteNodes.map((node) => (
          <Tooltip key={node.type} title={node.description} placement="right">
            <Card
              className="palette-node"
              draggable
              onDragStart={(e) => onDragStart(e, node)}
              onDoubleClick={() => onDoubleClick(node)}
              hoverable
              size="small"
            >
              <div className="node-info">
                <span
                  className="node-icon"
                  style={{ color: node.color }}
                >
                  {node.icon}
                </span>
                <Text>{node.label}</Text>
              </div>
            </Card>
          </Tooltip>
        ))}
      </Space>
      <div className="palette-hint">
        <Text type="secondary" style={{ fontSize: 11 }}>
          拖拽或双击添加节点
        </Text>
      </div>
    </div>
  )
}

// 创建默认节点数据
function createDefaultNodeData(type: WorkflowNode['type']): WorkflowNode['data'] {
  const baseData = { label: '', description: '' }

  switch (type) {
    case 'start':
      return { ...baseData, type: 'start', label: '开始' }
    case 'end':
      return { ...baseData, type: 'end', label: '结束' }
    case 'skill':
      return {
        ...baseData,
        type: 'skill',
        label: '技能节点',
        skillId: '',
        skillName: '',
        inputMapping: {},
        outputMapping: {},
      }
    case 'condition':
      return {
        ...baseData,
        type: 'condition',
        label: '条件判断',
        conditions: {
          expressions: [],
          logic: 'and',
        },
      }
    case 'transform':
      return {
        ...baseData,
        type: 'transform',
        label: '数据转换',
        expressions: [],
      }
    default:
      return baseData
  }
}
