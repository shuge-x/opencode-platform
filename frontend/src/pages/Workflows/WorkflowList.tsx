import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card,
  Table,
  Button,
  Space,
  Typography,
  Tag,
  message,
  Popconfirm,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useWorkflowStore, Workflow } from '@/stores/workflowStore'

const { Title } = Typography

// Mock 数据 - 后续替换为 API 调用
const mockWorkflows: Workflow[] = [
  {
    id: '1',
    name: '数据采集工作流',
    description: '从多个数据源采集数据并存储',
    nodes: [],
    edges: [],
    variables: [],
    is_active: true,
    created_at: '2026-02-15 10:00:00',
    updated_at: '2026-02-16 14:30:00',
  },
  {
    id: '2',
    name: '自动报告生成',
    description: '每周自动生成数据报告',
    nodes: [],
    edges: [],
    variables: [],
    is_active: true,
    created_at: '2026-02-14 09:00:00',
    updated_at: '2026-02-16 10:00:00',
  },
  {
    id: '3',
    name: '邮件提醒工作流',
    description: '监控异常并发送邮件提醒',
    nodes: [],
    edges: [],
    variables: [],
    is_active: false,
    created_at: '2026-02-10 15:00:00',
    updated_at: '2026-02-12 11:00:00',
  },
]

const WorkflowList: React.FC = () => {
  const navigate = useNavigate()
  const { setWorkflows } = useWorkflowStore()
  
  useEffect(() => {
    // 加载工作流列表
    setWorkflows(mockWorkflows)
  }, [setWorkflows])
  
  const handleCreate = () => {
    navigate('/workflows/new')
  }
  
  const handleEdit = (id: string) => {
    navigate(`/workflows/${id}/edit`)
  }
  
  const handleDelete = (id: string) => {
    message.success('工作流已删除')
    console.log('删除工作流:', id)
  }
  
  const handleExecute = (id: string) => {
    message.info('开始执行工作流...')
    console.log('执行工作流:', id)
  }
  
  const columns: ColumnsType<Workflow> = [
    {
      title: '工作流名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <strong>{text}</strong>,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'default'}>
          {isActive ? '已启用' : '已禁用'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<PlayCircleOutlined />}
            onClick={() => handleExecute(record.id)}
          >
            执行
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record.id)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确认删除"
            description="确定要删除这个工作流吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="删除"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]
  
  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px',
          }}
        >
          <Title level={3} style={{ margin: 0 }}>
            工作流列表
          </Title>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
          >
            新建工作流
          </Button>
        </div>
        
        <Table
          columns={columns}
          dataSource={mockWorkflows}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>
    </div>
  )
}

export default WorkflowList
