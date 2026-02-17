import React from 'react'
import { Layout, Typography, Button, Space, message } from 'antd'
import { SaveOutlined, PlayCircleOutlined, UndoOutlined } from '@ant-design/icons'
import Canvas from './Canvas'
import NodePalette from './NodePalette'
import NodeConfigPanel from './NodeConfigPanel'
import { useWorkflowStore } from '@/stores/workflowStore'

const { Header, Sider, Content } = Layout
const { Title } = Typography

const WorkflowEditor: React.FC = () => {
  const { nodes, edges, currentWorkflow } = useWorkflowStore()
  
  const handleSave = () => {
    const workflowData = {
      nodes,
      edges,
    }
    console.log('保存工作流:', workflowData)
    message.success('工作流已保存')
  }
  
  const handleExecute = () => {
    if (nodes.length === 0) {
      message.warning('请先添加节点')
      return
    }
    
    const hasStart = nodes.some(n => n.data.type === 'start')
    const hasEnd = nodes.some(n => n.data.type === 'end')
    
    if (!hasStart || !hasEnd) {
      message.warning('工作流必须包含开始和结束节点')
      return
    }
    
    message.info('开始执行工作流...')
    console.log('执行工作流:', { nodes, edges })
  }
  
  const handleReset = () => {
    useWorkflowStore.getState().reset()
    message.success('已重置工作流')
  }
  
  return (
    <Layout style={{ height: '100vh', overflow: 'hidden' }}>
      <Header
        style={{
          background: '#fff',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #f0f0f0',
          height: '64px',
        }}
      >
        <Title level={4} style={{ margin: 0 }}>
          {currentWorkflow?.name || '新建工作流'}
        </Title>
        
        <Space>
          <Button icon={<UndoOutlined />} onClick={handleReset}>
            重置
          </Button>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={handleSave}
          >
            保存
          </Button>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={handleExecute}
            style={{ background: '#52c41a', borderColor: '#52c41a' }}
          >
            执行
          </Button>
        </Space>
      </Header>
      
      <Layout>
        <Sider
          width={240}
          style={{
            background: '#fff',
            borderRight: '1px solid #f0f0f0',
          }}
        >
          <NodePalette />
        </Sider>
        
        <Content style={{ background: '#f5f5f5' }}>
          <Canvas />
        </Content>
        
        <Sider
          width={280}
          style={{
            background: '#fff',
            borderLeft: '1px solid #f0f0f0',
          }}
        >
          <NodeConfigPanel />
        </Sider>
      </Layout>
    </Layout>
  )
}

export default WorkflowEditor
