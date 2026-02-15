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
  message,
  Popconfirm,
  Card,
  Badge,
  Descriptions,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { rateLimitApi } from '@/api/gateway'
import type { RateLimit, RateLimitStrategy, RateLimitKeyType, CreateRateLimitRequest } from '@/types/gateway'

const strategies: { value: RateLimitStrategy; label: string; description: string }[] = [
  { value: 'fixed_window', label: '固定窗口', description: '在固定时间窗口内计数' },
  { value: 'sliding_window', label: '滑动窗口', description: '平滑的滑动时间窗口' },
  { value: 'token_bucket', label: '令牌桶', description: '按速率补充令牌' },
  { value: 'leaky_bucket', label: '漏桶', description: '恒定速率处理请求' },
]

const keyTypes: { value: RateLimitKeyType; label: string }[] = [
  { value: 'ip', label: '按IP地址' },
  { value: 'user', label: '按用户ID' },
  { value: 'api_key', label: '按API密钥' },
  { value: 'global', label: '全局限制' },
]

const strategyColors: Record<RateLimitStrategy, string> = {
  fixed_window: 'blue',
  sliding_window: 'cyan',
  token_bucket: 'green',
  leaky_bucket: 'orange',
}

export default function RateLimitConfig() {
  const [modalVisible, setModalVisible] = useState(false)
  const [detailVisible, setDetailVisible] = useState(false)
  const [editingRule, setEditingRule] = useState<RateLimit | null>(null)
  const [selectedRule, setSelectedRule] = useState<RateLimit | null>(null)
  const [searchText, setSearchText] = useState('')
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  // 获取限流规则列表
  const { data, isLoading } = useQuery({
    queryKey: ['gateway-rate-limits', searchText],
    queryFn: () => rateLimitApi.list({ search: searchText, pageSize: 100 }),
  })

  // 创建限流规则
  const createMutation = useMutation({
    mutationFn: (request: CreateRateLimitRequest) => rateLimitApi.create(request),
    onSuccess: () => {
      message.success('限流规则创建成功')
      queryClient.invalidateQueries({ queryKey: ['gateway-rate-limits'] })
      setModalVisible(false)
      form.resetFields()
    },
    onError: () => {
      message.error('限流规则创建失败')
    },
  })

  // 更新限流规则
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateRateLimitRequest> }) =>
      rateLimitApi.update(id, data),
    onSuccess: () => {
      message.success('限流规则更新成功')
      queryClient.invalidateQueries({ queryKey: ['gateway-rate-limits'] })
      setModalVisible(false)
      setEditingRule(null)
      form.resetFields()
    },
    onError: () => {
      message.error('限流规则更新失败')
    },
  })

  // 删除限流规则
  const deleteMutation = useMutation({
    mutationFn: (id: string) => rateLimitApi.delete(id),
    onSuccess: () => {
      message.success('限流规则删除成功')
      queryClient.invalidateQueries({ queryKey: ['gateway-rate-limits'] })
    },
    onError: () => {
      message.error('限流规则删除失败')
    },
  })

  // 切换状态
  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      rateLimitApi.toggle(id, enabled),
    onSuccess: () => {
      message.success('状态更新成功')
      queryClient.invalidateQueries({ queryKey: ['gateway-rate-limits'] })
    },
    onError: () => {
      message.error('状态更新失败')
    },
  })

  const handleCreate = () => {
    setEditingRule(null)
    form.resetFields()
    form.setFieldsValue({
      strategy: 'fixed_window',
      keyType: 'ip',
      windowSize: 60,
      maxRequests: 100,
      enabled: true,
    })
    setModalVisible(true)
  }

  const handleEdit = (rule: RateLimit) => {
    setEditingRule(rule)
    form.setFieldsValue({
      name: rule.name,
      description: rule.description,
      strategy: rule.strategy,
      keyType: rule.keyType,
      windowSize: rule.windowSize,
      maxRequests: rule.maxRequests,
      enabled: rule.enabled,
    })
    setModalVisible(true)
  }

  const handleViewDetail = (rule: RateLimit) => {
    setSelectedRule(rule)
    setDetailVisible(true)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingRule) {
        updateMutation.mutate({ id: editingRule.id, data: values })
      } else {
        createMutation.mutate(values)
      }
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const handleToggle = (rule: RateLimit, enabled: boolean) => {
    toggleMutation.mutate({ id: rule.id, enabled })
  }

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id)
  }

  const formatWindowSize = (seconds: number) => {
    if (seconds < 60) return `${seconds}秒`
    if (seconds < 3600) return `${seconds / 60}分钟`
    return `${seconds / 3600}小时`
  }

  const columns = [
    {
      title: '规则名称',
      dataIndex: 'name',
      key: 'name',
      width: 180,
      render: (name: string, record: RateLimit) => (
        <Space>
          <Badge status={record.enabled ? 'success' : 'default'} />
          <a onClick={() => handleViewDetail(record)}>{name}</a>
        </Space>
      ),
    },
    {
      title: '策略类型',
      dataIndex: 'strategy',
      key: 'strategy',
      width: 120,
      render: (strategy: RateLimitStrategy) => (
        <Tag color={strategyColors[strategy]}>
          {strategies.find((s) => s.value === strategy)?.label || strategy}
        </Tag>
      ),
    },
    {
      title: '限制类型',
      dataIndex: 'keyType',
      key: 'keyType',
      width: 120,
      render: (keyType: RateLimitKeyType) => (
        <Tag>{keyTypes.find((k) => k.value === keyType)?.label || keyType}</Tag>
      ),
    },
    {
      title: '时间窗口',
      dataIndex: 'windowSize',
      key: 'windowSize',
      width: 100,
      render: (windowSize: number) => (
        <Space>
          <ClockCircleOutlined />
          {formatWindowSize(windowSize)}
        </Space>
      ),
    },
    {
      title: '请求限制',
      dataIndex: 'maxRequests',
      key: 'maxRequests',
      width: 120,
      render: (maxRequests: number) => (
        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
          {maxRequests.toLocaleString()} 次
        </span>
      ),
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 100,
      render: (enabled: boolean, record: RateLimit) => (
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
      width: 150,
      render: (_: unknown, record: RateLimit) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="确定删除此限流规则?"
            description="删除后将无法恢复"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <Card
      title="限流配置"
      extra={
        <Space>
          <Input.Search
            placeholder="搜索限流规则..."
            onSearch={setSearchText}
            style={{ width: 200 }}
            allowClear
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            创建规则
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

      {/* 创建/编辑限流规则弹窗 */}
      <Modal
        title={editingRule ? '编辑限流规则' : '创建限流规则'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setModalVisible(false)
          setEditingRule(null)
        }}
        width={600}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="规则名称"
            rules={[{ required: true, message: '请输入规则名称' }]}
          >
            <Input placeholder="如：用户API限流" />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="规则描述信息" />
          </Form.Item>

          <Form.Item
            name="strategy"
            label="限流策略"
            rules={[{ required: true, message: '请选择限流策略' }]}
          >
            <Select>
              {strategies.map((s) => (
                <Select.Option key={s.value} value={s.value}>
                  <div>
                    <Tag color={strategyColors[s.value]}>{s.label}</Tag>
                    <span style={{ fontSize: 12, color: '#999' }}>{s.description}</span>
                  </div>
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="keyType"
            label="限制类型"
            rules={[{ required: true, message: '请选择限制类型' }]}
          >
            <Select>
              {keyTypes.map((k) => (
                <Select.Option key={k.value} value={k.value}>
                  {k.label}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="windowSize"
            label="时间窗口 (秒)"
            rules={[{ required: true, message: '请设置时间窗口' }]}
          >
            <InputNumber
              min={1}
              max={86400}
              style={{ width: '100%' }}
              placeholder="如：60 表示60秒"
            />
          </Form.Item>

          <Form.Item
            name="maxRequests"
            label="最大请求数"
            rules={[{ required: true, message: '请设置最大请求数' }]}
          >
            <InputNumber
              min={1}
              max={1000000}
              style={{ width: '100%' }}
              placeholder="在时间窗口内允许的最大请求数"
            />
          </Form.Item>

          <Form.Item name="enabled" label="启用状态" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情弹窗 */}
      <Modal
        title="限流规则详情"
        open={detailVisible}
        onCancel={() => {
          setDetailVisible(false)
          setSelectedRule(null)
        }}
        footer={null}
        width={600}
      >
        {selectedRule && (
          <Descriptions column={2} bordered>
            <Descriptions.Item label="规则名称" span={2}>
              {selectedRule.name}
            </Descriptions.Item>
            <Descriptions.Item label="描述" span={2}>
              {selectedRule.description || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="策略类型">
              <Tag color={strategyColors[selectedRule.strategy]}>
                {strategies.find((s) => s.value === selectedRule.strategy)?.label}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="限制类型">
              <Tag>{keyTypes.find((k) => k.value === selectedRule.keyType)?.label}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="时间窗口">
              {formatWindowSize(selectedRule.windowSize)}
            </Descriptions.Item>
            <Descriptions.Item label="最大请求数">
              {selectedRule.maxRequests.toLocaleString()} 次
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Badge status={selectedRule.enabled ? 'success' : 'default'} />
              {selectedRule.enabled ? '已启用' : '已禁用'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {new Date(selectedRule.createdAt).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {new Date(selectedRule.updatedAt).toLocaleString()}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </Card>
  )
}
