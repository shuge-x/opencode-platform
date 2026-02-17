import React from 'react'
import { Card, Form, Input, Select, Button, Space, Typography, Divider, Empty } from 'antd'
import { DeleteOutlined, SaveOutlined } from '@ant-design/icons'
import { useWorkflowStore, WorkflowNodeData } from '@/stores/workflowStore'
import { Node } from '@xyflow/react'

const { Title, Text } = Typography
const { TextArea } = Input

const NodeConfigPanel: React.FC = () => {
  const { nodes, selectedNode, updateNode, removeNode } = useWorkflowStore()
  const [form] = Form.useForm()
  
  const currentNode = nodes.find((n: Node<WorkflowNodeData>) => n.id === selectedNode)
  
  React.useEffect(() => {
    if (currentNode) {
      form.setFieldsValue({
        label: currentNode.data.label,
        skillName: currentNode.data.skillName,
        config: currentNode.data.config,
      })
    }
  }, [currentNode, form])
  
  if (!currentNode) {
    return (
      <Card style={{ height: '100%' }} styles={{ body: { padding: '16px' } }}>
        <Empty
          description="请选择一个节点"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    )
  }
  
  const handleValuesChange = (values: any) => {
    if (currentNode) {
      updateNode(currentNode.id, values)
    }
  }
  
  const handleDelete = () => {
    if (currentNode) {
      removeNode(currentNode.id)
    }
  }
  
  const getNodeTypeInfo = () => {
    switch (currentNode.data.type) {
      case 'start':
        return { color: '#52c41a', text: '开始节点' }
      case 'end':
        return { color: '#ff4d4f', text: '结束节点' }
      case 'skill':
        return { color: '#1890ff', text: '技能节点' }
      default:
        return { color: '#8c8c8c', text: '未知节点' }
    }
  }
  
  const nodeInfo = getNodeTypeInfo()
  
  return (
    <Card
      style={{ height: '100%', overflow: 'auto' }}
      styles={{ body: { padding: '16px' } }}
    >
      <Title level={4}>节点配置</Title>
      
      <Divider style={{ margin: '12px 0' }} />
      
      <div style={{ marginBottom: '16px' }}>
        <Text type="secondary">节点类型：</Text>
        <Text strong style={{ color: nodeInfo.color, marginLeft: '8px' }}>
          {nodeInfo.text}
        </Text>
      </div>
      
      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleValuesChange}
        initialValues={{
          label: currentNode.data.label,
          skillName: currentNode.data.skillName,
        }}
      >
        <Form.Item label="节点名称" name="label">
          <Input placeholder="请输入节点名称" />
        </Form.Item>
        
        {currentNode.data.type === 'skill' && (
          <>
            <Form.Item label="技能名称" name="skillName">
              <Input placeholder="请输入技能名称" />
            </Form.Item>
            
            <Divider style={{ margin: '12px 0' }} />
            
            <Form.Item label="配置参数">
              <TextArea
                rows={4}
                placeholder="JSON 格式的配置参数"
                onChange={(e) => {
                  try {
                    const config = JSON.parse(e.target.value)
                    updateNode(currentNode.id, { config })
                  } catch (err) {
                    // Invalid JSON, ignore
                  }
                }}
                defaultValue={JSON.stringify(currentNode.data.config || {}, null, 2)}
              />
            </Form.Item>
          </>
        )}
        
        <Divider style={{ margin: '16px 0' }} />
        
        <Space direction="vertical" style={{ width: '100%' }}>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            block
            onClick={() => {
              form.submit()
            }}
          >
            保存配置
          </Button>
          
          <Button
            danger
            icon={<DeleteOutlined />}
            block
            onClick={handleDelete}
          >
            删除节点
          </Button>
        </Space>
      </Form>
    </Card>
  )
}

export default NodeConfigPanel
