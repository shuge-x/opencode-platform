import React, { memo } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import { ThunderboltOutlined } from '@ant-design/icons'
import { Typography, Tag } from 'antd'
import { WorkflowNodeData } from '@/stores/workflowStore'

const { Text } = Typography

const SkillNode: React.FC<NodeProps<WorkflowNodeData>> = ({ data, selected }) => {
  return (
    <div
      style={{
        padding: '12px 20px',
        borderRadius: '8px',
        background: 'linear-gradient(135deg, #1890ff 0%, #40a9ff 100%)',
        border: selected ? '2px solid #faad14' : '2px solid #1890ff',
        boxShadow: selected ? '0 4px 12px rgba(24, 144, 255, 0.4)' : '0 2px 8px rgba(0, 0, 0, 0.1)',
        minWidth: '150px',
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        style={{
          background: '#fff',
          border: '2px solid #1890ff',
          width: '10px',
          height: '10px',
        }}
      />
      
      <Handle
        type="source"
        position={Position.Bottom}
        style={{
          background: '#fff',
          border: '2px solid #1890ff',
          width: '10px',
          height: '10px',
        }}
      />
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <ThunderboltOutlined style={{ fontSize: '20px', color: '#fff' }} />
        <Text strong style={{ color: '#fff', margin: 0 }}>
          {data.label || '技能节点'}
        </Text>
      </div>
      
      {data.skillName && (
        <Tag color="blue" style={{ marginTop: '4px', border: 'none' }}>
          {data.skillName}
        </Tag>
      )}
    </div>
  )
}

export default memo(SkillNode)
