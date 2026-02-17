import React, { useState, useEffect } from 'react'
import {
  Card,
  Descriptions,
  Tag,
  Space,
  Button,
  Typography,
  Empty,
  Spin,
  Timeline,
  Collapse,
  Row,
  Col,
  Statistic,
  Divider,
  Alert,
  Tooltip,
  Steps,
  Tabs,
  message,
} from 'antd'
import {
  ArrowLeftOutlined,
  PlayCircleOutlined,
  ClockCircleOutlined,
  ApiOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  StopOutlined,
  CopyOutlined,
  DownloadOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import type { WorkflowExecution, ExecutionStep, ExecutionStatus } from '@/types/workflow'
import { getExecution, cancelExecution } from '@/api/workflows'
import './ExecutionDetail.css'

const { Title, Text, Paragraph } = Typography
const { Panel } = Collapse

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
  webhook: 'Webhook 触发',
}

// 节点类型文本
const NODE_TYPE_TEXT: Record<string, string> = {
  start: '开始',
  end: '结束',
  skill: '技能节点',
  condition: '条件节点',
  transform: '数据变换',
}

// 格式化持续时间
const formatDuration = (start: string, end?: string): string => {
  const startTime = new Date(start).getTime()
  const endTime = end ? new Date(end).getTime() : Date.now()
  const durationMs = endTime - startTime

  if (durationMs < 1000) {
    return `${durationMs}ms`
  } else if (durationMs < 60000) {
    return `${(durationMs / 1000).toFixed(2)}s`
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

// 格式化 JSON 显示
const formatJson = (data: unknown): string => {
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

export default function ExecutionDetail() {
  const navigate = useNavigate()
  const { id: executionId } = useParams<{ id: string }>()

  const [loading, setLoading] = useState(false)
  const [execution, setExecution] = useState<WorkflowExecution | null>(null)

  // 加载执行详情
  const loadExecution = async () => {
    if (!executionId) return

    setLoading(true)
    try {
      const data = await getExecution(executionId)
      setExecution(data)
    } catch (error) {
      console.error('Failed to load execution:', error)
      // 使用 mock 数据
      setExecution(generateMockExecution())
    } finally {
      setLoading(false)
    }
  }

  // 生成 mock 数据
  const generateMockExecution = (): WorkflowExecution => {
    const statuses: ExecutionStatus[] = ['completed', 'failed', 'running']
    const status = statuses[Math.floor(Math.random() * statuses.length)]
    const startedAt = new Date(Date.now() - 5 * 60 * 1000)
    const finishedAt = status !== 'running'
      ? new Date(startedAt.getTime() + 45000)
      : undefined

    return {
      id: executionId || 'exec-1',
      workflow_id: 'wf-123',
      trigger_type: 'manual',
      status,
      input_data: {
        query: '搜索关键词',
        limit: 10,
      },
      output_data: status === 'completed' ? {
        results: ['结果1', '结果2', '结果3'],
        total: 100,
      } : undefined,
      started_at: startedAt.toISOString(),
      finished_at: finishedAt?.toISOString(),
      error_message: status === 'failed' ? '执行超时：超过最大等待时间' : undefined,
      steps: [
        {
          id: 'step-1',
          execution_id: executionId || 'exec-1',
          node_id: 'start-1',
          node_type: 'start',
          status: 'completed',
          input_data: {},
          output_data: {},
          started_at: startedAt.toISOString(),
          finished_at: startedAt.toISOString(),
        },
        {
          id: 'step-2',
          execution_id: executionId || 'exec-1',
          node_id: 'skill-1',
          node_type: 'skill',
          status: 'completed',
          input_data: { query: '搜索关键词' },
          output_data: { results: ['结果1', '结果2'] },
          started_at: new Date(startedAt.getTime() + 100).toISOString(),
          finished_at: new Date(startedAt.getTime() + 15000).toISOString(),
        },
        {
          id: 'step-3',
          execution_id: executionId || 'exec-1',
          node_id: 'transform-1',
          node_type: 'transform',
          status: status === 'failed' ? 'failed' : 'completed',
          input_data: { results: ['结果1', '结果2'] },
          output_data: status !== 'failed' ? { processed: ['处理1', '处理2'] } : undefined,
          started_at: new Date(startedAt.getTime() + 15100).toISOString(),
          finished_at: status !== 'running' ? new Date(startedAt.getTime() + 30000).toISOString() : undefined,
          error_message: status === 'failed' ? '转换失败：数据格式错误' : undefined,
        },
        {
          id: 'step-4',
          execution_id: executionId || 'exec-1',
          node_id: 'end-1',
          node_type: 'end',
          status: status === 'completed' ? 'completed' : 'pending',
          input_data: {},
          output_data: {},
          started_at: status === 'completed' ? new Date(startedAt.getTime() + 30100).toISOString() : '',
          finished_at: status === 'completed' ? new Date(startedAt.getTime() + 45000).toISOString() : undefined,
        },
      ],
    }
  }

  // 取消执行
  const handleCancel = async () => {
    if (!executionId) return

    try {
      await cancelExecution(executionId)
      message.success('已取消执行')
      loadExecution()
    } catch {
      message.error('取消失败')
    }
  }

  // 复制 JSON
  const handleCopyJson = (data: unknown) => {
    const json = formatJson(data)
    navigator.clipboard.writeText(json)
    message.success('已复制到剪贴板')
  }

  // 下载日志
  const handleDownloadLog = () => {
    if (!execution) return

    const log = `
执行详情
=========

执行ID: ${execution.id}
工作流ID: ${execution.workflow_id}
状态: ${STATUS_TEXT[execution.status]}
触发方式: ${TRIGGER_TEXT[execution.trigger_type]}
开始时间: ${formatDateTime(execution.started_at)}
${execution.finished_at ? `结束时间: ${formatDateTime(execution.finished_at)}` : ''}
持续时间: ${formatDuration(execution.started_at, execution.finished_at)}
${execution.error_message ? `\n错误信息: ${execution.error_message}` : ''}

输入数据
--------
${formatJson(execution.input_data)}

${execution.output_data ? `
输出数据
--------
${formatJson(execution.output_data)}
` : ''}

执行步骤
--------
${execution.steps.map((step, i) => `
步骤 ${i + 1}: ${NODE_TYPE_TEXT[step.node_type] || step.node_type}
  状态: ${STATUS_TEXT[step.status]}
  开始: ${step.started_at ? formatDateTime(step.started_at) : '-'}
  结束: ${step.finished_at ? formatDateTime(step.finished_at) : '-'}
  ${step.error_message ? `错误: ${step.error_message}` : ''}
`).join('')}
    `.trim()

    const blob = new Blob([log], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `execution-${executionId}.log`
    a.click()
    URL.revokeObjectURL(url)
  }

  // 返回列表
  const handleGoBack = () => {
    if (execution?.workflow_id) {
      navigate(`/workflows/${execution.workflow_id}/executions`)
    } else {
      navigate(-1)
    }
  }

  // 初始加载
  useEffect(() => {
    loadExecution()
  }, [executionId])

  // 渲染步骤时间线
  const renderStepsTimeline = () => {
    if (!execution?.steps.length) {
      return <Empty description="暂无执行步骤" />
    }

    return (
      <Timeline
        items={execution.steps.map((step) => ({
          color: STATUS_COLORS[step.status] === 'success' ? 'green' :
                 STATUS_COLORS[step.status] === 'error' ? 'red' :
                 STATUS_COLORS[step.status] === 'processing' ? 'blue' : 'gray',
          dot: STATUS_ICONS[step.status],
          children: (
            <div className="step-item">
              <div className="step-header">
                <Space>
                  <Text strong>{NODE_TYPE_TEXT[step.node_type] || step.node_type}</Text>
                  <Tag color={STATUS_COLORS[step.status]}>
                    {STATUS_TEXT[step.status]}
                  </Tag>
                </Space>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {step.started_at ? formatDuration(step.started_at, step.finished_at) : '-'}
                </Text>
              </div>
              <div className="step-details">
                <Text type="secondary" style={{ fontSize: 12 }}>
                  节点ID: {step.node_id}
                </Text>
                {step.error_message && (
                  <Alert
                    type="error"
                    message={step.error_message}
                    showIcon
                    style={{ marginTop: 8 }}
                  />
                )}
              </div>
            </div>
          ),
        }))}
      />
    )
  }

  // 渲染数据面板
  const renderDataPanel = (data: unknown, title: string) => (
    <div className="data-panel">
      <div className="data-panel-header">
        <Text strong>{title}</Text>
        <Button
          size="small"
          icon={<CopyOutlined />}
          onClick={() => handleCopyJson(data)}
        >
          复制
        </Button>
      </div>
      <pre className="json-viewer">{formatJson(data)}</pre>
    </div>
  )

  // Tab 项
  const tabItems = [
    {
      key: 'steps',
      label: (
        <span>
          <PlayCircleOutlined />
          执行步骤
        </span>
      ),
      children: renderStepsTimeline(),
    },
    {
      key: 'input',
      label: (
        <span>
          <InfoCircleOutlined />
          输入数据
        </span>
      ),
      children: execution && renderDataPanel(execution.input_data, '输入参数'),
    },
    {
      key: 'output',
      label: (
        <span>
          <CheckCircleOutlined />
          输出数据
        </span>
      ),
      children: execution?.output_data
        ? renderDataPanel(execution.output_data, '输出结果')
        : <Empty description="暂无输出数据" />,
      disabled: !execution?.output_data,
    },
  ]

  if (loading) {
    return (
      <div className="execution-detail-page loading">
        <Spin size="large" />
      </div>
    )
  }

  if (!execution) {
    return (
      <div className="execution-detail-page">
        <Empty description="执行记录不存在" />
      </div>
    )
  }

  return (
    <div className="execution-detail-page">
      {/* 页面标题 */}
      <div className="page-header">
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={handleGoBack}>
            返回
          </Button>
          <Title level={3} style={{ margin: 0 }}>
            执行详情
          </Title>
          <Tag
            icon={STATUS_ICONS[execution.status]}
            color={STATUS_COLORS[execution.status]}
          >
            {STATUS_TEXT[execution.status]}
          </Tag>
        </Space>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadExecution}
            loading={loading}
          >
            刷新
          </Button>
          <Button
            icon={<DownloadOutlined />}
            onClick={handleDownloadLog}
          >
            下载日志
          </Button>
          {execution.status === 'running' && (
            <Button
              danger
              icon={<StopOutlined />}
              onClick={handleCancel}
            >
              取消执行
            </Button>
          )}
        </Space>
      </div>

      {/* 错误提示 */}
      {execution.error_message && (
        <Alert
          type="error"
          message="执行失败"
          description={execution.error_message}
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 基本信息 */}
      <Card style={{ marginBottom: 16 }}>
        <Descriptions column={{ xs: 1, sm: 2, md: 4 }}>
          <Descriptions.Item label="执行ID">
            <Text code>{execution.id}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="工作流ID">
            <Text code>{execution.workflow_id}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="触发方式">
            <Space>
              {TRIGGER_ICONS[execution.trigger_type]}
              <Text>{TRIGGER_TEXT[execution.trigger_type]}</Text>
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={STATUS_COLORS[execution.status]}>
              {STATUS_TEXT[execution.status]}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="开始时间">
            {formatDateTime(execution.started_at)}
          </Descriptions.Item>
          <Descriptions.Item label="结束时间">
            {execution.finished_at ? formatDateTime(execution.finished_at) : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="持续时间">
            {formatDuration(execution.started_at, execution.finished_at)}
          </Descriptions.Item>
          <Descriptions.Item label="步骤数">
            {execution.steps.length}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="总步骤"
              value={execution.steps.length}
              prefix={<PlayCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="已完成"
              value={execution.steps.filter((s) => s.status === 'completed').length}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="执行中"
              value={execution.steps.filter((s) => s.status === 'running').length}
              valueStyle={{ color: '#1890ff' }}
              prefix={<LoadingOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="失败"
              value={execution.steps.filter((s) => s.status === 'failed').length}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<CloseCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 详情 Tabs */}
      <Card>
        <Tabs defaultActiveKey="steps" items={tabItems} />
      </Card>
    </div>
  )
}
