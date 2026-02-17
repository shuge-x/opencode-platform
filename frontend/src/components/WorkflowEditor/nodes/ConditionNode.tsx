import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { BranchesOutlined } from '@ant-design/icons'
import { Typography, Tag } from 'antd'
import type { ConditionNodeData } from '@/types/workflow'
import './NodeStyles.css'

const { Text } = Typography

const ConditionNode = memo(({ data, selected }: NodeProps<ConditionNodeData>) => {
  const conditionCount = data.conditions?.expressions?.length || 0

  return (
    <div
      className={`workflow-node condition-node ${selected ? 'selected' : ''}`}
    >
      <Handle type="target" position={Position.Top} className="node-handle" />
      <div className="node-icon">
        <BranchesOutlined />
      </div>
      <div className="node-content">
        <Text strong className="node-label">
          {data.label || '条件判断'}
        </Text>
        {data.description && (
          <Text type="secondary" className="node-description">
            {data.description}
          </Text>
        )}
        <div className="node-tags">
          <Tag color="orange" className="node-tag">
            {conditionCount} 个条件
          </Tag>
        </div>
      </div>
      {/* True 输出 */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="true"
        className="node-handle true-handle"
        style={{ left: '30%' }}
      />
      <div className="handle-label true-label" style={{ left: '30%' }}>
        ✓ {data.trueLabel || '是'}
      </div>
      {/* False 输出 */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="false"
        className="node-handle false-handle"
        style={{ left: '70%' }}
      />
      <div className="handle-label false-label" style={{ left: '70%' }}>
        ✗ {data.falseLabel || '否'}
      </div>
    </div>
  )
})

ConditionNode.displayName = 'ConditionNode'

export default ConditionNode
