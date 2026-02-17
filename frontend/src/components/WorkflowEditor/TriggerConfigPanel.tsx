import React, { useState, useEffect } from 'react'
import {
  Card,
  Form,
  Select,
  Input,
  Switch,
  Button,
  Space,
  Typography,
  Divider,
  message,
  Tooltip,
  Alert,
  Row,
  Col,
} from 'antd'
import {
  PlayCircleOutlined,
  ClockCircleOutlined,
  ApiOutlined,
  CopyOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import type { Workflow } from '@/types/workflow'

const { Text, Paragraph } = Typography
const { Option } = Select

export type TriggerType = 'manual' | 'scheduled' | 'webhook'

export interface TriggerConfig {
  type: TriggerType
  enabled: boolean
  cronExpression?: string
  webhookToken?: string
}

interface TriggerConfigPanelProps {
  workflowId: string
  workflow?: Workflow
  initialConfig?: TriggerConfig
  onSave?: (config: TriggerConfig) => Promise<void>
  onTrigger?: () => Promise<void>
  loading?: boolean
}

// Cron 表达式预设
const CRON_PRESETS = [
  { label: '每小时', value: '0 * * * *', description: '每小时整点执行' },
  { label: '每天凌晨', value: '0 0 * * *', description: '每天 00:00 执行' },
  { label: '每天中午', value: '0 12 * * *', description: '每天 12:00 执行' },
  { label: '每周一凌晨', value: '0 0 * * 1', description: '每周一 00:00 执行' },
  { label: '每月1号凌晨', value: '0 0 1 * *', description: '每月1号 00:00 执行' },
  { label: '每5分钟', value: '*/5 * * * *', description: '每5分钟执行一次' },
  { label: '每15分钟', value: '*/15 * * * *', description: '每15分钟执行一次' },
  { label: '每30分钟', value: '*/30 * * * *', description: '每30分钟执行一次' },
]

// Cron 字段说明
const CRON_FIELD_DESCRIPTIONS = [
  { field: '分钟', range: '0-59', example: '*/15' },
  { field: '小时', range: '0-23', example: '9' },
  { field: '日期', range: '1-31', example: '1' },
  { field: '月份', range: '1-12', example: '*' },
  { field: '星期', range: '0-6', example: '1-5' },
]

// 验证 Cron 表达式（基础验证）
const validateCronExpression = (expression: string): { valid: boolean; error?: string } => {
  const parts = expression.trim().split(/\s+/)
  if (parts.length !== 5) {
    return { valid: false, error: 'Cron 表达式必须包含 5 个字段' }
  }
  
  // 简单验证每个字段
  const patterns = [
    /^(\*|([0-9]|[1-5][0-9])(-([0-9]|[1-5][0-9]))?(,([0-9]|[1-5][0-9])(-([0-9]|[1-5][0-9]))?)*|(\*\/[0-9]+))$/,
    /^(\*|([0-9]|1[0-9]|2[0-3])(-([0-9]|1[0-9]|2[0-3]))?(,([0-9]|1[0-9]|2[0-3])(-([0-9]|1[0-9]|2[0-3]))?)*|(\*\/[0-9]+))$/,
    /^(\*|([1-9]|[12][0-9]|3[01])(-([1-9]|[12][0-9]|3[01]))?(,([1-9]|[12][0-9]|3[01])(-([1-9]|[12][0-9]|3[01]))?)*|(\*\/[0-9]+))$/,
    /^(\*|([1-9]|1[0-2])(-([1-9]|1[0-2]))?(,([1-9]|1[0-2])(-([1-9]|1[0-2]))?)*|(\*\/[0-9]+))$/,
    /^(\*|[0-6](-[0-6])?(,[0-6](-[0-6])?)*|(\*\/[0-9]+))$/,
  ]
  
  for (let i = 0; i < parts.length; i++) {
    if (!patterns[i].test(parts[i])) {
      return { valid: false, error: `第 ${i + 1} 个字段 "${parts[i]}" 格式无效` }
    }
  }
  
  return { valid: true }
}

// 解析 Cron 表达式为人类可读的描述
const parseCronDescription = (expression: string): string => {
  const parts = expression.trim().split(/\s+/)
  if (parts.length !== 5) return expression
  
  const [minute, hour, dayOfMonth, month, dayOfWeek] = parts
  
  // 简单解析逻辑
  if (minute === '*' && hour === '*' && dayOfMonth === '*' && month === '*' && dayOfWeek === '*') {
    return '每分钟'
  }
  if (minute === '0' && hour === '*' && dayOfMonth === '*' && month === '*' && dayOfWeek === '*') {
    return '每小时整点'
  }
  if (minute === '0' && hour === '0' && dayOfMonth === '*' && month === '*' && dayOfWeek === '*') {
    return '每天凌晨 00:00'
  }
  if (minute === '0' && hour === '12' && dayOfMonth === '*' && month === '*' && dayOfWeek === '*') {
    return '每天中午 12:00'
  }
  if (minute.startsWith('*/')) {
    const interval = minute.slice(2)
    return `每 ${interval} 分钟`
  }
  
  return `${minute} ${hour} ${dayOfMonth} ${month} ${dayOfWeek}`
}

export default function TriggerConfigPanel({
  workflowId,
  workflow,
  initialConfig,
  onSave,
  onTrigger,
  loading = false,
}: TriggerConfigPanelProps) {
  const [form] = Form.useForm()
  const [config, setConfig] = useState<TriggerConfig>(
    initialConfig || {
      type: 'manual',
      enabled: true,
    }
  )
  const [webhookCopied, setWebhookCopied] = useState(false)
  const [cronError, setCronError] = useState<string | undefined>()

  // 生成 Webhook URL
  const webhookUrl = config.webhookToken
    ? `${window.location.origin}/api/v1/webhooks/${config.webhookToken}`
    : ''

  // 生成新的 Webhook Token
  const generateWebhookToken = () => {
    const token = `${workflowId}-${Date.now().toString(36)}-${Math.random().toString(36).substr(2, 9)}`
    setConfig((prev) => ({ ...prev, webhookToken: token }))
  }

  // 处理触发类型变更
  const handleTypeChange = (type: TriggerType) => {
    const newConfig: TriggerConfig = {
      ...config,
      type,
    }
    
    if (type === 'webhook' && !config.webhookToken) {
      newConfig.webhookToken = `${workflowId}-${Date.now().toString(36)}-${Math.random().toString(36).substr(2, 9)}`
    }
    
    if (type === 'scheduled' && !config.cronExpression) {
      newConfig.cronExpression = '0 * * * *'
    }
    
    setConfig(newConfig)
    setCronError(undefined)
  }

  // 处理 Cron 表达式变更
  const handleCronChange = (value: string) => {
    setConfig((prev) => ({ ...prev, cronExpression: value }))
    
    if (value) {
      const validation = validateCronExpression(value)
      setCronError(validation.valid ? undefined : validation.error)
    } else {
      setCronError(undefined)
    }
  }

  // 复制 Webhook URL
  const handleCopyWebhook = async () => {
    try {
      await navigator.clipboard.writeText(webhookUrl)
      setWebhookCopied(true)
      message.success('已复制到剪贴板')
      setTimeout(() => setWebhookCopied(false), 2000)
    } catch {
      message.error('复制失败，请手动复制')
    }
  }

  // 保存配置
  const handleSave = async () => {
    if (config.type === 'scheduled' && config.cronExpression) {
      const validation = validateCronExpression(config.cronExpression)
      if (!validation.valid) {
        message.error(validation.error)
        return
      }
    }
    
    try {
      await onSave?.(config)
      message.success('触发器配置已保存')
    } catch {
      message.error('保存失败')
    }
  }

  // 立即执行
  const handleTrigger = async () => {
    try {
      await onTrigger?.()
      message.success('工作流已触发执行')
    } catch {
      message.error('触发执行失败')
    }
  }

  // 触发类型图标
  const getTriggerIcon = (type: TriggerType) => {
    switch (type) {
      case 'manual':
        return <PlayCircleOutlined />
      case 'scheduled':
        return <ClockCircleOutlined />
      case 'webhook':
        return <ApiOutlined />
    }
  }

  useEffect(() => {
    if (initialConfig) {
      setConfig(initialConfig)
    }
  }, [initialConfig])

  return (
    <Card
      title={
        <Space>
          <span>触发器配置</span>
          <Tooltip title="配置工作流的触发方式">
            <InfoCircleOutlined style={{ color: '#999' }} />
          </Tooltip>
        </Space>
      }
      extra={
        <Space>
          <Button onClick={handleSave} loading={loading} type="primary">
            保存配置
          </Button>
          {config.type === 'manual' && onTrigger && (
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={handleTrigger}
              loading={loading}
            >
              立即执行
            </Button>
          )}
        </Space>
      }
    >
      <Form form={form} layout="vertical">
        {/* 启用开关 */}
        <Form.Item label="启用触发器">
          <Switch
            checked={config.enabled}
            onChange={(checked) => setConfig((prev) => ({ ...prev, enabled: checked }))}
            checkedChildren="启用"
            unCheckedChildren="禁用"
          />
        </Form.Item>

        <Divider />

        {/* 触发类型选择 */}
        <Form.Item label="触发类型">
          <Select
            value={config.type}
            onChange={handleTypeChange}
            style={{ width: '100%' }}
            disabled={!config.enabled}
          >
            <Option value="manual">
              <Space>
                <PlayCircleOutlined />
                <span>手动触发</span>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  - 点击按钮执行
                </Text>
              </Space>
            </Option>
            <Option value="scheduled">
              <Space>
                <ClockCircleOutlined />
                <span>定时触发</span>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  - 按 Cron 表达式执行
                </Text>
              </Space>
            </Option>
            <Option value="webhook">
              <Space>
                <ApiOutlined />
                <span>Webhook 触发</span>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  - HTTP 请求触发
                </Text>
              </Space>
            </Option>
          </Select>
        </Form.Item>

        {/* 定时触发配置 */}
        {config.type === 'scheduled' && (
          <div style={{ marginTop: 16 }}>
            <Form.Item
              label={
                <Space>
                  <span>Cron 表达式</span>
                  <Tooltip title={
                    <div>
                      <div>格式: 分钟 小时 日期 月份 星期</div>
                      <div style={{ marginTop: 8 }}>
                        {CRON_FIELD_DESCRIPTIONS.map((f) => (
                          <div key={f.field}>
                            {f.field}: {f.range} (例: {f.example})
                          </div>
                        ))}
                      </div>
                    </div>
                  }>
                    <InfoCircleOutlined style={{ color: '#999' }} />
                  </Tooltip>
                </Space>
              }
              validateStatus={cronError ? 'error' : undefined}
              help={cronError}
            >
              <Input
                value={config.cronExpression}
                onChange={(e) => handleCronChange(e.target.value)}
                placeholder="* * * * *"
                disabled={!config.enabled}
                status={cronError ? 'error' : undefined}
              />
            </Form.Item>

            {/* Cron 预设 */}
            <Form.Item label="快速选择">
              <Select
                placeholder="选择预设时间"
                style={{ width: '100%' }}
                onChange={(value) => handleCronChange(value)}
                disabled={!config.enabled}
                allowClear
              >
                {CRON_PRESETS.map((preset) => (
                  <Option key={preset.value} value={preset.value}>
                    <Space direction="vertical" size={0}>
                      <span>{preset.label}</span>
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {preset.description}
                      </Text>
                    </Space>
                  </Option>
                ))}
              </Select>
            </Form.Item>

            {/* Cron 解析说明 */}
            {config.cronExpression && !cronError && (
              <Alert
                type="info"
                showIcon
                message={
                  <Space>
                    <span>执行计划:</span>
                    <Text strong>{parseCronDescription(config.cronExpression)}</Text>
                  </Space>
                }
                style={{ marginBottom: 16 }}
              />
            )}
          </div>
        )}

        {/* Webhook 配置 */}
        {config.type === 'webhook' && (
          <div style={{ marginTop: 16 }}>
            <Form.Item label="Webhook URL">
              <Input.Group compact>
                <Input
                  style={{ width: 'calc(100% - 100px)' }}
                  value={webhookUrl}
                  readOnly
                  disabled={!config.enabled}
                />
                <Button
                  icon={webhookCopied ? <CheckCircleOutlined /> : <CopyOutlined />}
                  onClick={handleCopyWebhook}
                  disabled={!webhookUrl || !config.enabled}
                  style={{ width: 100 }}
                  type={webhookCopied ? 'primary' : 'default'}
                >
                  {webhookCopied ? '已复制' : '复制'}
                </Button>
              </Input.Group>
            </Form.Item>

            <Form.Item label="Webhook Token">
              <Input
                value={config.webhookToken}
                onChange={(e) => setConfig((prev) => ({ ...prev, webhookToken: e.target.value }))}
                placeholder="Webhook Token"
                disabled={!config.enabled}
              />
              <Button
                type="link"
                onClick={generateWebhookToken}
                disabled={!config.enabled}
                style={{ padding: '4px 0' }}
              >
                重新生成 Token
              </Button>
            </Form.Item>

            <Alert
              type="info"
              showIcon
              message="使用方法"
              description={
                <div>
                  <Paragraph style={{ marginBottom: 8 }}>
                    向上述 URL 发送 POST 请求即可触发工作流执行:
                  </Paragraph>
                  <pre style={{
                    background: '#f5f5f5',
                    padding: 8,
                    borderRadius: 4,
                    fontSize: 12,
                    overflow: 'auto'
                  }}>
{`curl -X POST "${webhookUrl}" \\
  -H "Content-Type: application/json" \\
  -d '{"input": {"key": "value"}}'`}
                  </pre>
                </div>
              }
            />
          </div>
        )}

        {/* 手动触发说明 */}
        {config.type === 'manual' && (
          <Alert
            type="info"
            showIcon
            message="手动触发"
            description="点击右上角的「立即执行」按钮或在工作流详情页触发执行"
          />
        )}
      </Form>

      {/* 当前配置摘要 */}
      <Divider />
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Text type="secondary">触发类型:</Text>
          <br />
          <Space>
            {getTriggerIcon(config.type)}
            <Text strong>
              {config.type === 'manual' && '手动触发'}
              {config.type === 'scheduled' && '定时触发'}
              {config.type === 'webhook' && 'Webhook 触发'}
            </Text>
          </Space>
        </Col>
        <Col span={12}>
          <Text type="secondary">状态:</Text>
          <br />
          <Text strong style={{ color: config.enabled ? '#52c41a' : '#ff4d4f' }}>
            {config.enabled ? '已启用' : '已禁用'}
          </Text>
        </Col>
        {config.type === 'scheduled' && config.cronExpression && (
          <Col span={24}>
            <Text type="secondary">执行计划:</Text>
            <br />
            <Text code>{config.cronExpression}</Text>
            {!cronError && (
              <Text type="secondary" style={{ marginLeft: 8 }}>
                ({parseCronDescription(config.cronExpression)})
              </Text>
            )}
          </Col>
        )}
      </Row>
    </Card>
  )
}
