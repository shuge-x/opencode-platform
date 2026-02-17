import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { TransformOutlined } from '@ant-design/icons'
import { Typography, Tag } from 'antd'
import type { TransformNodeData } from '@/types/workflow'
import './NodeStyles.css'

const { Text } = Typography

const TransformNode = memo(({ data, selected }: NodeProps<TransformNodeData>) => {
  const transformCount = data.expressions?.length || 0

  return (
    <div
      className={`workflow-node transform-node ${selected ? 'selected' : ''}`}
    >
      <Handle type="target" position={Position.Top} className="node-handle" />
      <div className="node-icon">
        <TransformOutlined />
      </div>
      <div className="node-content">
        <Text strong className="node-label">
          {data.label || '数据转换'}
        </Text>
        {data.description && (
          <Text type="secondary" className="node-description">
            {data.description}
          </Text>
        )}
        <div className="node-tags">
          <Tag color="purple" className="node-tag">
            {transformCount} 个转换
          </Tag>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="node-handle" />
    </div>
  )
})

TransformNode.displayName = 'TransformNode'

export default TransformNode
