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
  DatePicker,
  message,
  Popconfirm,
  Card,
  Badge,
  Typography,
  Tooltip,
  Descriptions,
  Line,
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  CopyOutlined,
  KeyOutlined,
  LineChartOutlined,
  ReloadOutlined,
  EyeOutlined,
  EyeTw00Outlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { apiKeyApi } from '@/api/gateway'
import type { ApiKey, ApiKeyUsage, CreateApiKeyRequest } from '@/types/gateway'

const { Text, Paragraph } = Typography
const { RangePicker } = DatePicker

const scopeOptions = [
  { value: 'read', label: '读取权限', color: 'blue' },
  { value: 'write', label: '写入权限', color: 'green' },
  { value: 'admin', label: '管理权限', color: 'red' },
  { value: 'analytics', label: '分析权限', color: 'purple' },
]

export default function ApiKeyManager() {
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [usageModalVisible, setUsageModalVisible] = useState(false)
  const [newKeyData, setNewKeyData] = useState<ApiKey | null>(null)
  const [selectedKey, setSelectedKey] = useState<ApiKey | null>(null)
  const [searchText, setSearchText] = useState('')
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  // 获取密钥列表
  const { data, isLoading } = useQuery({
    queryKey: ['gateway-api-keys', searchText],
    queryFn: () => apiKeyApi.list({ search: searchText, pageSize: 100 }),
  })

  // 获取密钥使用统计
  const { data: usageData, isLoading: usageLoading } = useQuery({
    queryKey: ['gateway-api-key-usage', selectedKey?.id, dateRange],
    queryFn: () =>
      apiKeyApi.getUsage(selectedKey!.id, {
        startDate: dateRange?.[0].format('YYYY-MM-DD'),
        endDate: dateRange?.[1].format('YYYY-MM-DD'),
      }),
    enabled: !!selectedKey && usageModalVisible,
  })

  // 创建密钥
  const createMutation = useMutation({
    mutationFn: (request: CreateApiKeyRequest) => apiKeyApi.create(request),
    onSuccess: (data) => {
      message.success('API密钥创建成功')
      queryClient.invalidateQueries({ queryKey: ['gateway-api-keys'] })
      setNewKeyData(data)
      form.resetFields()
    },
    onError: () => {
      message.error('API密钥创建失败')
    },
  })

  // 删除密钥
  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiKeyApi.delete(id),
    onSuccess: () => {
      message.success('API密钥删除成功')
      queryClient.invalidateQueries({ queryKey: ['gateway-api-keys'] })
    },
    onError: () => {
      message.error('API密钥删除失败')
    },
  })

  // 切换状态
  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      apiKeyApi.toggle(id, enabled),
    onSuccess: () => {
      message.success('状态更新成功')
      queryClient.invalidateQueries({ queryKey: ['gateway-api-keys'] })
    },
    onError: () => {
      message.error('状态更新失败')
    },
  })

  // 重新生成密钥
  const regenerateMutation = useMutation({
    mutationFn: (id: string) => apiKeyApi.regenerate(id),
    onSuccess: (data) => {
      message.success('密钥已重新生成')
      queryClient.invalidateQueries({ queryKey: ['gateway-api-keys'] })
      setNewKeyData(data)
    },
    onError: () => {
      message.error('密钥重新生成失败')
    },
  })

  const handleCreate = () => {
    form.resetFields()
    form.setFieldsValue({
      scopes: ['read'],
    })
    setNewKeyData(null)
    setCreateModalVisible(true)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const request: CreateApiKeyRequest = {
        ...values,
        expiresAt: values.expiresAt?.toISOString(),
      }
      createMutation.mutate(request)
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const handleViewDetail = (key: ApiKey) => {
    setSelectedKey(key)
    setDetailModalVisible(true)
  }

  const handleViewUsage = (key: ApiKey) => {
    setSelectedKey(key)
    setDateRange([dayjs().subtract(7, 'day'), dayjs()])
    setUsageModalVisible(true)
  }

  const handleToggle = (key: ApiKey, enabled: boolean) => {
    toggleMutation.mutate({ id: key.id, enabled })
  }

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id)
  }

  const handleRegenerate = (id: string) => {
    regenerateMutation.mutate(id)
  }

  const handleCopyKey = (key: string) => {
    navigator.clipboard.writeText(key)
    message.success('密钥已复制到剪贴板')
  }

  const maskKey = (key: string) => {
    if (key.length <= 12) return key
    return `${key.slice(0, 8)}...${key.slice(-4)}`
  }

  const columns = [
    {
      title: '密钥名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (name: string, record: ApiKey) => (
        <Space>
          <Badge status={record.enabled ? 'success' : 'default'} />
          <KeyOutlined />
          <a onClick={() => handleViewDetail(record)}>{name}</a>
        </Space>
      ),
    },
    {
      title: '密钥',
      dataIndex: 'key',
      key: 'key',
      width: 200,
      render: (key: string) => (
        <Space>
          <Text code>{maskKey(key)}</Text>
          <Tooltip title="复制密钥">
            <Button
              type="text"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => handleCopyKey(key)}
            />
          </Tooltip>
        </Space>
      ),
    },
    {
      title: '权限范围',
      dataIndex: 'scopes',
      key: 'scopes',
      width: 200,
      render: (scopes: string[]) => (
        <Space size={4} wrap>
          {scopes.map((scope) => {
            const option = scopeOptions.find((s) => s.value === scope)
            return (
              <Tag key={scope} color={option?.color || 'default'}>
                {option?.label || scope}
              </Tag>
            )
          })}
        </Space>
      ),
    },
    {
      title: '使用次数',
      dataIndex: 'usageCount',
      key: 'usageCount',
      width: 100,
      render: (count: number) => (
        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
          {count.toLocaleString()}
        </span>
      ),
    },
    {
      title: '最后使用',
      dataIndex: 'lastUsedAt',
      key: 'lastUsedAt',
      width: 150,
      render: (date: string) => (date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '-'),
    },
    {
      title: '过期时间',
      dataIndex: 'expiresAt',
      key: 'expiresAt',
      width: 150,
      render: (date: string) => {
        if (!date) return <Tag>永不过期</Tag>
        const isExpired = dayjs(date).isBefore(dayjs())
        return (
          <Tag color={isExpired ? 'red' : 'green'}>
            {isExpired ? '已过期' : dayjs(date).format('YYYY-MM-DD')}
          </Tag>
        )
      },
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 100,
      render: (enabled: boolean, record: ApiKey) => (
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
      width: 200,
      render: (_: unknown, record: ApiKey) => (
        <Space>
          <Tooltip title="查看统计">
            <Button
              type="text"
              icon={<LineChartOutlined />}
              onClick={() => handleViewUsage(record)}
            />
          </Tooltip>
          <Tooltip title="重新生成">
            <Popconfirm
              title="确定重新生成密钥?"
              description="原密钥将立即失效"
              onConfirm={() => handleRegenerate(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button type="text" icon={<ReloadOutlined />} />
            </Popconfirm>
          </Tooltip>
          <Popconfirm
            title="确定删除此密钥?"
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
      title="API 密钥管理"
      extra={
        <Space>
          <Input.Search
            placeholder="搜索密钥..."
            onSearch={setSearchText}
            style={{ width: 200 }}
            allowClear
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            生成新密钥
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

      {/* 创建密钥弹窗 */}
      <Modal
        title="生成新 API 密钥"
        open={createModalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setCreateModalVisible(false)
          setNewKeyData(null)
        }}
        width={600}
        confirmLoading={createMutation.isPending}
        okText={newKeyData ? '关闭' : '生成'}
        okButtonProps={{ style: { display: newKeyData ? 'none' : undefined } }}
      >
        {newKeyData ? (
          <div style={{ padding: '20px 0' }}>
            <div style={{ marginBottom: 16, color: '#52c41a', fontWeight: 'bold' }}>
              ✓ API密钥创建成功！请妥善保存以下密钥，关闭后将无法再次查看完整密钥。
            </div>
            <Paragraph copyable={{ text: newKeyData.key }}>
              <Text code style={{ fontSize: 16, wordBreak: 'break-all' }}>
                {newKeyData.key}
              </Text>
            </Paragraph>
            <Button type="primary" onClick={() => setCreateModalVisible(false)}>
              我已保存，关闭窗口
            </Button>
          </div>
        ) : (
          <Form form={form} layout="vertical">
            <Form.Item
              name="name"
              label="密钥名称"
              rules={[{ required: true, message: '请输入密钥名称' }]}
            >
              <Input placeholder="如：生产环境API密钥" />
            </Form.Item>

            <Form.Item name="description" label="描述">
              <Input.TextArea rows={2} placeholder="密钥用途描述" />
            </Form.Item>

            <Form.Item
              name="scopes"
              label="权限范围"
              rules={[{ required: true, message: '请选择权限范围' }]}
            >
              <Select mode="multiple" placeholder="选择权限">
                {scopeOptions.map((s) => (
                  <Select.Option key={s.value} value={s.value}>
                    <Tag color={s.color}>{s.label}</Tag>
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item name="rateLimitId" label="限流规则">
              <Select placeholder="选择关联的限流规则（可选）" allowClear>
                {/* 这里应该从限流规则列表获取 */}
              </Select>
            </Form.Item>

            <Form.Item name="expiresAt" label="过期时间">
              <DatePicker
                showTime
                style={{ width: '100%' }}
                placeholder="不选择表示永不过期"
                disabledDate={(current) => current && current < dayjs().endOf('day')}
              />
            </Form.Item>
          </Form>
        )}
      </Modal>

      {/* 详情弹窗 */}
      <Modal
        title="密钥详情"
        open={detailModalVisible}
        onCancel={() => {
          setDetailModalVisible(false)
          setSelectedKey(null)
        }}
        footer={null}
        width={600}
      >
        {selectedKey && (
          <Descriptions column={2} bordered>
            <Descriptions.Item label="密钥名称" span={2}>
              {selectedKey.name}
            </Descriptions.Item>
            <Descriptions.Item label="描述" span={2}>
              {selectedKey.description || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="密钥" span={2}>
              <Text code>{maskKey(selectedKey.key)}</Text>
              <Button
                type="link"
                size="small"
                icon={<CopyOutlined />}
                onClick={() => handleCopyKey(selectedKey.key)}
              >
                复制
              </Button>
            </Descriptions.Item>
            <Descriptions.Item label="权限范围" span={2}>
              <Space size={4}>
                {selectedKey.scopes.map((scope) => {
                  const option = scopeOptions.find((s) => s.value === scope)
                  return (
                    <Tag key={scope} color={option?.color || 'default'}>
                      {option?.label || scope}
                    </Tag>
                  )
                })}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="使用次数">
              {selectedKey.usageCount.toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Badge status={selectedKey.enabled ? 'success' : 'default'} />
              {selectedKey.enabled ? '已启用' : '已禁用'}
            </Descriptions.Item>
            <Descriptions.Item label="最后使用时间">
              {selectedKey.lastUsedAt
                ? dayjs(selectedKey.lastUsedAt).format('YYYY-MM-DD HH:mm:ss')
                : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="过期时间">
              {selectedKey.expiresAt
                ? dayjs(selectedKey.expiresAt).format('YYYY-MM-DD HH:mm:ss')
                : '永不过期'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {dayjs(selectedKey.createdAt).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {dayjs(selectedKey.updatedAt).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 使用统计弹窗 */}
      <Modal
        title="密钥使用统计"
        open={usageModalVisible}
        onCancel={() => {
          setUsageModalVisible(false)
          setSelectedKey(null)
        }}
        footer={null}
        width={800}
      >
        <Space style={{ marginBottom: 16 }}>
          <RangePicker
            value={dateRange}
            onChange={(dates) => setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
          />
        </Space>
        <Table
          columns={[
            {
              title: '日期',
              dataIndex: 'date',
              key: 'date',
              render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
            },
            {
              title: '请求数',
              dataIndex: 'requestCount',
              key: 'requestCount',
              render: (count: number) => count.toLocaleString(),
            },
            {
              title: '错误数',
              dataIndex: 'errorCount',
              key: 'errorCount',
              render: (count: number) => (
                <Text type={count > 0 ? 'danger' : undefined}>{count}</Text>
              ),
            },
            {
              title: '平均延迟',
              dataIndex: 'avgLatency',
              key: 'avgLatency',
              render: (latency: number) => `${latency.toFixed(2)}ms`,
            },
          ]}
          dataSource={usageData || []}
          rowKey="date"
          loading={usageLoading}
          pagination={false}
          size="small"
        />
      </Modal>
    </Card>
  )
}
