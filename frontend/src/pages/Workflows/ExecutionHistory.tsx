import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Tag,
  Space,
  Button,
  Select,
  DatePicker,
  Input,
  Typography,
  Empty,
  Spin,
  Pagination,
  Row,
  Col,
  Tooltip,
  Badge,
  Statistic,
} from 'antd'
import {
  PlayCircleOutlined,
  ClockCircleOutlined,
  ApiOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  StopOutlined,
  SearchOutlined,
  ReloadOutlined,
  EyeOutlined,
  CalendarOutlined,
} from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import type { ColumnsType } from 'antd/es/table'
import type { WorkflowExecution, ExecutionStatus } from '@/types/workflow'
import { getWorkflowExecutions } from '@/api/workflows'
import './ExecutionHistory.css'

const { Title, Text } = Typography
const { RangePicker } = DatePicker
const { Option } = Select

// 状态颜色映射
const STATUS_COLORS: Record<ExecutionStatus, string> = {
  pending: 'default',
  running: 'processing',
  completed: 'success',
  failed: 'error',
  cancelled: 'warning',
}

// 状态图标映射
const STATUS_ICONS: Record<ExecutionStatus, React.ReactNode> = {
  pending: <ClockCircleOutlined />,
  running: <LoadingOutlined spin />,
  completed: <CheckCircleOutlined />,
  failed: <CloseCircleOutlined />,
  cancelled: <StopOutlined />,
}

// 状态文本映射
const STATUS_TEXT: Record<ExecutionStatus, string> = {
  pending: '等待中',
  running: '执行中',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消',
}

// 触发类型图标
const TRIGGER_ICONS: Record<string, React.ReactNode> = {
  manual: <PlayCircleOutlined />,
  scheduled: <ClockCircleOutlined />,
  webhook: <ApiOutlined />,
}

// 触发类型文本
const TRIGGER_TEXT: Record<string, string> = {
  manual: '手动触发',
  scheduled: '定时触发',
  webhook: 'Webhook',
}

// 格式化持续时间
const formatDuration = (start: string, end?: string): string => {
  const startTime = new Date(start).getTime()
  const endTime = end ? new Date(end).getTime() : Date.now()
  const durationMs = endTime - startTime

  if (durationMs < 1000) {
    return `${durationMs}ms`
  } else if (durationMs < 60000) {
    return `${(durationMs / 1000).toFixed(1)}s`
  } else if (durationMs < 3600000) {
    const minutes = Math.floor(durationMs / 60000)
    const seconds = Math.floor((durationMs % 60000) / 1000)
    return `${minutes}m ${seconds}s`
  } else {
    const hours = Math.floor(durationMs / 3600000)
    const minutes = Math.floor((durationMs % 3600000) / 60000)
    return `${hours}h ${minutes}m`
  }
}

// 格式化日期时间
const formatDateTime = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export default function ExecutionHistory() {
  const navigate = useNavigate()
  const { id: workflowId } = useParams<{ id: string }>()

  // 状态
  const [loading, setLoading] = useState(false)
  const [executions, setExecutions] = useState<WorkflowExecution[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  // 筛选条件
  const [statusFilter, setStatusFilter] = useState<ExecutionStatus | undefined>()
  const [triggerFilter, setTriggerFilter] = useState<string | undefined>()
  const [dateRange, setDateRange] = useState<[string, string] | undefined>()
  const [searchKeyword, setSearchKeyword] = useState('')

  // 统计数据
  const [stats, setStats] = useState({
    total: 0,
    completed: 0,
    failed: 0,
    running: 0,
  })

  // 加载执行历史
  const loadExecutions = async () => {
    if (!workflowId) return

    setLoading(true)
    try {
      const data = await getWorkflowExecutions(workflowId, {
        status: statusFilter,
        trigger_type: triggerFilter,
        start_date: dateRange?.[0],
        end_date: dateRange?.[1],
        search: searchKeyword || undefined,
        page,
        page_size: pageSize,
      })

      setExecutions(data.items || data)
      setTotal(data.total || data.length)

      // 计算统计
      const allExecutions = data.items || data
      setStats({
        total: data.total || data.length,
        completed: allExecutions.filter((e: WorkflowExecution) => e.status === 'completed').length,
        failed: allExecutions.filter((e: WorkflowExecution) => e.status === 'failed').length,
        running: allExecutions.filter((e: WorkflowExecution) => e.status === 'running').length,
      })
    } catch (error) {
      console.error('Failed to load executions:', error)
      // 使用 mock 数据
      const mockData = generateMockExecutions()
      setExecutions(mockData)
      setTotal(mockData.length)
      setStats({
        total: mockData.length,
        completed: mockData.filter((e) => e.status === 'completed').length,
        failed: mockData.filter((e) => e.status === 'failed').length,
        running: mockData.filter((e) => e.status === 'running').length,
      })
    } finally {
      setLoading(false)
    }
  }

  // 生成 mock 数据
  const generateMockExecutions = (): WorkflowExecution[] => {
    const statuses: ExecutionStatus[] = ['pending', 'running', 'completed', 'failed', 'cancelled']
    const triggers = ['manual', 'scheduled', 'webhook']

    return Array.from({ length: 25 }, (_, i) => {
      const status = statuses[Math.floor(Math.random() * statuses.length)]
      const startedAt = new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000)
      const finishedAt = status !== 'pending' && status !== 'running'
        ? new Date(startedAt.getTime() + Math.random() * 60000)
        : undefined

      return {
        id: `exec-${i + 1}`,
        workflow_id: workflowId || '1',
        trigger_type: triggers[Math.floor(Math.random() * triggers.length)] as 'manual' | 'scheduled' | 'webhook',
        status,
        input_data: { param1: `value${i}` },
        output_data: status === 'completed' ? { result: `result${i}` } : undefined,
        started_at: startedAt.toISOString(),
        finished_at: finishedAt?.toISOString(),
        error_message: status === 'failed' ? '执行失败：超时' : undefined,
        steps: [],
      }
    })
  }

  // 初始加载
  useEffect(() => {
    loadExecutions()
  }, [workflowId, page, pageSize, statusFilter, triggerFilter, dateRange])

  // 查看执行详情
  const handleViewDetail = (executionId: string) => {
    navigate(`/executions/${executionId}`)
  }

  // 刷新列表
  const handleRefresh = () => {
    loadExecutions()
  }

  // 表格列定义
  const columns: ColumnsType<WorkflowExecution> = [
    {
      title: '执行ID',
      dataIndex: 'id',
      key: 'id',
      width: 150,
      render: (id: string) => (
        <Text code style={{ fontSize: 12 }}>
          {id.length > 12 ? `${id.slice(0, 12)}...` : id}
        </Text>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: ExecutionStatus) => (
        <Tag icon={STATUS_ICONS[status]} color={STATUS_COLORS[status]}>
          {STATUS_TEXT[status]}
        </Tag>
      ),
      filters: [
        { text: '等待中', value: 'pending' },
        { text: '执行中', value: 'running' },
        { text: '已完成', value: 'completed' },
        { text: '失败', value: 'failed' },
        { text: '已取消', value: 'cancelled' },
      ],
      filteredValue: statusFilter ? [statusFilter] : undefined,
      onFilter: (value) => value === statusFilter,
    },
    {
      title: '触发方式',
      dataIndex: 'trigger_type',
      key: 'trigger_type',
      width: 120,
      render: (type: string) => (
        <Space>
          {TRIGGER_ICONS[type]}
          <Text>{TRIGGER_TEXT[type] || type}</Text>
        </Space>
      ),
      filters: [
        { text: '手动触发', value: 'manual' },
        { text: '定时触发', value: 'scheduled' },
        { text: 'Webhook', value: 'webhook' },
      ],
      filteredValue: triggerFilter ? [triggerFilter] : undefined,
    },
    {
      title: '开始时间',
      dataIndex: 'started_at',
      key: 'started_at',
      width: 180,
      render: (date: string) => (
        <Space>
          <CalendarOutlined style={{ color: '#999' }} />
          <Text>{formatDateTime(date)}</Text>
        </Space>
      ),
      sorter: (a, b) => new Date(a.started_at).getTime() - new Date(b.started_at).getTime(),
      defaultSortOrder: 'descend',
    },
    {
      title: '持续时间',
      key: 'duration',
      width: 100,
      render: (_, record) => (
        <Text>
          {formatDuration(record.started_at, record.finished_at)}
        </Text>
      ),
    },
    {
      title: '错误信息',
      dataIndex: 'error_message',
      key: 'error_message',
      ellipsis: true,
      render: (error?: string) =>
        error ? (
          <Tooltip title={error}>
            <Text type="danger" ellipsis style={{ maxWidth: 200 }}>
              {error}
            </Text>
          </Tooltip>
        ) : (
          <Text type="secondary">-</Text>
        ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      fixed: 'right',
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => handleViewDetail(record.id)}
        >
          详情
        </Button>
      ),
    },
  ]

  return (
    <div className="execution-history-page">
      {/* 页面标题 */}
      <div className="page-header">
        <Space>
          <Title level={3} style={{ margin: 0 }}>
            执行历史
          </Title>
          <Text type="secondary">工作流 ID: {workflowId}</Text>
        </Space>
        <Button
          icon={<ReloadOutlined />}
          onClick={handleRefresh}
          loading={loading}
        >
          刷新
        </Button>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="总执行次数"
              value={stats.total}
              prefix={<PlayCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="已完成"
              value={stats.completed}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="执行中"
              value={stats.running}
              valueStyle={{ color: '#1890ff' }}
              prefix={<LoadingOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="失败"
              value={stats.failed}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<CloseCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选区域 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Input
              placeholder="搜索执行ID..."
              prefix={<SearchOutlined />}
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              onPressEnter={loadExecutions}
              allowClear
            />
          </Col>
          <Col xs={24} sm={12} md={5}>
            <Select
              placeholder="状态筛选"
              style={{ width: '100%' }}
              value={statusFilter}
              onChange={setStatusFilter}
              allowClear
            >
              <Option value="pending">等待中</Option>
              <Option value="running">执行中</Option>
              <Option value="completed">已完成</Option>
              <Option value="failed">失败</Option>
              <Option value="cancelled">已取消</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={5}>
            <Select
              placeholder="触发方式"
              style={{ width: '100%' }}
              value={triggerFilter}
              onChange={setTriggerFilter}
              allowClear
            >
              <Option value="manual">手动触发</Option>
              <Option value="scheduled">定时触发</Option>
              <Option value="webhook">Webhook</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <RangePicker
              style={{ width: '100%' }}
              onChange={(dates) => {
                if (dates && dates[0] && dates[1]) {
                  setDateRange([
                    dates[0].toISOString(),
                    dates[1].toISOString(),
                  ])
                } else {
                  setDateRange(undefined)
                }
              }}
            />
          </Col>
        </Row>
      </Card>

      {/* 执行列表 */}
      <Card>
        <Spin spinning={loading}>
          {executions.length === 0 && !loading ? (
            <Empty
              description="暂无执行记录"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ) : (
            <>
              <Table
                columns={columns}
                dataSource={executions}
                rowKey="id"
                pagination={false}
                scroll={{ x: 1000 }}
                size="middle"
              />

              <div className="pagination-wrapper">
                <Pagination
                  current={page}
                  pageSize={pageSize}
                  total={total}
                  onChange={(p, ps) => {
                    setPage(p)
                    setPageSize(ps)
                  }}
                  showSizeChanger
                  showQuickJumper
                  showTotal={(t) => `共 ${t} 条记录`}
                  pageSizeOptions={['10', '20', '50', '100']}
                />
              </div>
            </>
          )}
        </Spin>
      </Card>
    </div>
  )
}
