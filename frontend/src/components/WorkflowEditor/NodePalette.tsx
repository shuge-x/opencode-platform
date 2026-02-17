import React from 'react'
import { Card, Typography, Space, Divider } from 'antd'
import {
  PlayCircleOutlined,
  StopOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { DragEvent } from 'react'

const { Title, Text } = Typography

interface NodeItemProps {
  type: string
  label: string
  icon: React.ReactNode
  color: string
  description: string
}

const NodeItem: React.FC<NodeItemProps> = ({
  type,
  label,
  icon,
  color,
  description,
}) => {
  const onDragStart = (event: DragEvent<HTMLDivElement>, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType)
    event.dataTransfer.effectAllowed = 'move'
  }

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, type)}
      style={{
        padding: '12px',
        borderRadius: '8px',
        background: '#fff',
        border: '1px solid #d9d9d9',
        cursor: 'grab',
        transition: 'all 0.3s',
        marginBottom: '8px',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = color
        e.currentTarget.style.boxShadow = `0 2px 8px ${color}33`
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = '#d9d9d9'
        e.currentTarget.style.boxShadow = 'none'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{ color, fontSize: '20px' }}>{icon}</div>
        <div>
          <Text strong style={{ display: 'block' }}>
            {label}
          </Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {description}
          </Text>
        </div>
      </div>
    </div>
  )
}

const NodePalette: React.FC = () => {
  return (
    <Card
      style={{
        height: '100%',
        overflow: 'auto',
      }}
      styles={{
        body: { padding: '16px' }
      }}
    >
      <Title level={4} style={{ marginBottom: '16px' }}>
        节点面板
      </Title>
      
      <Divider style={{ margin: '12px 0' }} />
      
      <Space direction="vertical" style={{ width: '100%' }}>
        <Text type="secondary" style={{ fontSize: '12px' }}>
          拖拽节点到画布
        </Text>
        
        <NodeItem
          type="start"
          label="开始节点"
          icon={<PlayCircleOutlined />}
          color="#52c41a"
          description="工作流的起点"
        />
        
        <NodeItem
          type="end"
          label="结束节点"
          icon={<StopOutlined />}
          color="#ff4d4f"
          description="工作流的终点"
        />
        
        <NodeItem
          type="skill"
          label="技能节点"
          icon={<ThunderboltOutlined />}
          color="#1890ff"
          description="执行一个技能"
        />
      </Space>
      
      <Divider style={{ margin: '16px 0' }} />
      
      <div style={{ marginTop: '16px' }}>
        <Text type="secondary" style={{ fontSize: '12px' }}>
          提示：从左侧拖拽节点到画布上使用
        </Text>
      </div>
    </Card>
  )
}

export default NodePalette
