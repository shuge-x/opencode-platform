import React, { memo } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import { StopOutlined } from '@ant-design/icons'
import { Typography, Tag } from 'antd'
import { WorkflowNodeData } from '@/stores/workflowStore'

const { Text } = Typography

const EndNode: React.FC<NodeProps<WorkflowNodeData>> = ({ data, selected }) => {
  return (
    <div
      style={{
        padding: '12px 20px',
        borderRadius: '8px',
        background: 'linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%)',
        border: selected ? '2px solid #1890ff' : '2px solid #ff4d4f',
        boxShadow: selected ? '0 4px 12px rgba(255, 77, 79, 0.4)' : '0 2px 8px rgba(0, 0, 0, 0.1)',
        minWidth: '120px',
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        style={{
          background: '#fff',
          border: '2px solid #ff4d4f',
          width: '10px',
          height: '10px',
        }}
      />
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <StopOutlined style={{ fontSize: '20px', color: '#fff' }} />
        <Text strong style={{ color: '#fff', margin: 0 }}>
          {data.label || '结束'}
        </Text>
      </div>
      
      <Tag color="red" style={{ marginTop: '4px', border: 'none' }}>
        流程终点
      </Tag>
    </div>
  )
}

export default memo(EndNode)
