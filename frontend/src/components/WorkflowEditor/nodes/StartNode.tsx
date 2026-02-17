import React, { memo } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import { PlayCircleOutlined } from '@ant-design/icons'
import { Typography, Tag } from 'antd'
import { WorkflowNodeData } from '@/stores/workflowStore'

const { Text } = Typography

const StartNode: React.FC<NodeProps<WorkflowNodeData>> = ({ data, selected }) => {
  return (
    <div
      style={{
        padding: '12px 20px',
        borderRadius: '8px',
        background: 'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)',
        border: selected ? '2px solid #1890ff' : '2px solid #52c41a',
        boxShadow: selected ? '0 4px 12px rgba(82, 196, 26, 0.4)' : '0 2px 8px rgba(0, 0, 0, 0.1)',
        minWidth: '120px',
      }}
    >
      <Handle
        type="source"
        position={Position.Bottom}
        style={{
          background: '#fff',
          border: '2px solid #52c41a',
          width: '10px',
          height: '10px',
        }}
      />
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <PlayCircleOutlined style={{ fontSize: '20px', color: '#fff' }} />
        <Text strong style={{ color: '#fff', margin: 0 }}>
          {data.label || '开始'}
        </Text>
      </div>
      
      <Tag color="green" style={{ marginTop: '4px', border: 'none' }}>
        流程起点
      </Tag>
    </div>
  )
}

export default memo(StartNode)
