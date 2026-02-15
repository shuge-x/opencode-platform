import React, { useState } from 'react'
import {
  Table,
  Button,
  Space,
  Tag,
  Switch,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Tooltip,
  message,
  Popconfirm,
  Card,
  Badge,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ThunderboltOutlined,
  ApiOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { routeApi } from '@/api/gateway'
import type { RouteRule, HttpMethod, CreateRouteRequest } from '@/types/gateway'

const httpMethods: HttpMethod[] = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
const methodColors: Record<HttpMethod, string> = {
  GET: 'green',
  POST: 'blue',
  PUT: 'orange',
  DELETE: 'red',
  PATCH: 'cyan',
  HEAD: 'purple',
  OPTIONS: 'default',
}

interface RouteListProps {
  onTestRoute?: (route: RouteRule) => void
}

export default function RouteList({ onTestRoute }: RouteListProps) {
  const [modalVisible, setModalVisible] = useState(false)
  const [editingRoute, setEditingRoute] = useState<RouteRule | null>(null)
  const [searchText, setSearchText] = useState('')
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  // 获取路由列表
  const { data, isLoading } = useQuery({
    queryKey: ['gateway-routes', searchText],
    queryFn: () => routeApi.list({ search: searchText, pageSize: 100 }),
  })

  // 创建路由
  const createMutation = useMutation({
    mutationFn: (request: CreateRouteRequest) => routeApi.create(request),
    onSuccess: () => {
      message.success('路由创建成功')
      queryClient.invalidateQueries({ queryKey: ['gateway-routes'] })
      setModalVisible(false)
      form.resetFields()
    },
    onError: () => {
      message.error('路由创建失败')
    },
  })

  // 更新路由
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateRouteRequest> }) =>
      routeApi.update(id, data),
    onSuccess: () => {
      message.success('路由更新成功')
      queryClient.invalidateQueries({ queryKey: ['gateway-routes'] })
      setModalVisible(false)
      setEditingRoute(null)
      form.resetFields()
    },
    onError: () => {
      message.error('路由更新失败')
    },
  })

  // 删除路由
  const deleteMutation = useMutation({
    mutationFn: (id: string) => routeApi.delete(id),
    onSuccess: () => {
      message.success('路由删除成功')
      queryClient.invalidateQueries({ queryKey: ['gateway-routes'] })
    },
    onError: () => {
      message.error('路由删除失败')
    },
  })

  // 切换状态
  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      routeApi.toggle(id, enabled),
    onSuccess: () => {
      message.success('状态更新成功')
      queryClient.invalidateQueries({ queryKey: ['gateway-routes'] })
    },
    onError: () => {
      message.error('状态更新失败')
    },
  })

  const handleCreate = () => {
    setEditingRoute(null)
    form.resetFields()
    form.setFieldsValue({
      methods: ['GET'],
      priority: 100,
      enabled: true,
      authRequired: false,
      timeout: 30000,
      retryCount: 3,
    })
    setModalVisible(true)
  }

  const handleEdit = (route: RouteRule) => {
    setEditingRoute(route)
    form.setFieldsValue({
      name: route.name,
      description: route.description,
      path: route.path,
      methods: route.methods,
      target: route.target,
      priority: route.priority,
      enabled: route.enabled,
      authRequired: route.authRequired,
      timeout: route.timeout,
      retryCount: route.retryCount,
    })
    setModalVisible(true)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingRoute) {
        updateMutation.mutate({ id: editingRoute.id, data: values })
      } else {
        createMutation.mutate(values)
      }
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const handleToggle = (route: RouteRule, enabled: boolean) => {
    toggleMutation.mutate({ id: route.id, enabled })
  }

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id)
  }

  const columns = [
    {
      title: '路由名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (name: string, record: RouteRule) => (
        <Space>
          <Badge status={record.enabled ? 'success' : 'default'} />
          <span>{name}</span>
        </Space>
      ),
    },
    {
      title: '路径',
      dataIndex: 'path',
      key: 'path',
      width: 200,
      render: (path: string) => (
        <Tooltip title={path}>
          <code style={{ background: '#f5f5f5', padding: '2px 8px', borderRadius: 4 }}>
            {path.length > 30 ? `...${path.slice(-30)}` : path}
          </code>
        </Tooltip>
      ),
    },
    {
      title: '请求方法',
      dataIndex: 'methods',
      key: 'methods',
      width: 180,
      render: (methods: HttpMethod[]) => (
        <Space size={4} wrap>
          {methods.map((method) => (
            <Tag key={method} color={methodColors[method]}>
              {method}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '转发目标',
      dataIndex: 'target',
      key: 'target',
      ellipsis: true,
      render: (target: string) => (
        <Tooltip title={target}>
          <ApiOutlined style={{ marginRight: 4 }} />
          {target}
        </Tooltip>
      ),
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      sorter: (a: RouteRule, b: RouteRule) => a.priority - b.priority,
    },
    {
      title: '认证',
      dataIndex: 'authRequired',
      key: 'authRequired',
      width: 80,
      render: (required: boolean) => (
        <Tag color={required ? 'orange' : 'default'}>
          {required ? '需要' : '无需'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 100,
      render: (enabled: boolean, record: RouteRule) => (
        <Switch
          checked={enabled}
          onChange={(checked) => handleToggle(record, checked)}
          loading={toggleMutation.isPending}
        />
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_: unknown, record: RouteRule) => (
        <Space>
          <Tooltip title="测试路由">
            <Button
              type="text"
              icon={<ThunderboltOutlined />}
              onClick={() => onTestRoute?.(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定删除此路由?"
            description="删除后将无法恢复"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <Card
      title="路由规则列表"
      extra={
        <Space>
          <Input.Search
            placeholder="搜索路由..."
            onSearch={setSearchText}
            style={{ width: 200 }}
            allowClear
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            创建路由
          </Button>
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={data?.data || []}
        rowKey="id"
        loading={isLoading}
        pagination={{
          total: data?.total || 0,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`,
        }}
      />

      <Modal
        title={editingRoute ? '编辑路由' : '创建路由'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setModalVisible(false)
          setEditingRoute(null)
        }}
        width={600}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="路由名称"
            rules={[{ required: true, message: '请输入路由名称' }]}
          >
            <Input placeholder="如：用户API路由" />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="路由描述信息" />
          </Form.Item>

          <Form.Item
            name="path"
            label="路径模式"
            rules={[{ required: true, message: '请输入路径模式' }]}
            help="支持路径参数，如 /api/users/:id"
          >
            <Input placeholder="/api/v1/users/*" />
          </Form.Item>

          <Form.Item
            name="methods"
            label="请求方法"
            rules={[{ required: true, message: '请选择请求方法' }]}
          >
            <Select mode="multiple" placeholder="选择支持的HTTP方法">
              {httpMethods.map((method) => (
                <Select.Option key={method} value={method}>
                  <Tag color={methodColors[method]}>{method}</Tag>
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="target"
            label="转发目标"
            rules={[
              { required: true, message: '请输入转发目标地址' },
              { type: 'url', message: '请输入有效的URL' },
            ]}
            help="如：http://backend-service:8080"
          >
            <Input placeholder="http://backend-service:8080/api" />
          </Form.Item>

          <Form.Item
            name="priority"
            label="优先级"
            rules={[{ required: true, message: '请设置优先级' }]}
            help="数值越大优先级越高"
          >
            <InputNumber min={1} max={1000} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="authRequired" label="需要认证" valuePropName="checked">
            <Switch />
          </Form.Item>

          <Form.Item name="enabled" label="启用状态" valuePropName="checked">
            <Switch />
          </Form.Item>

          <Form.Item
            name="timeout"
            label="超时时间 (ms)"
            rules={[{ required: true, message: '请设置超时时间' }]}
          >
            <InputNumber min={1000} max={300000} step={1000} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="retryCount"
            label="重试次数"
            rules={[{ required: true, message: '请设置重试次数' }]}
          >
            <InputNumber min={0} max={10} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
