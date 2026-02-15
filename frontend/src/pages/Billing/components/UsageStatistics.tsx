import { Card, Row, Col, Statistic, Table, Typography, Space } from 'antd'
import {
  PhoneOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  DollarOutlined,
} from '@ant-design/icons'
import type { UsageStatistics as UsageStatisticsType, UsageBySkill } from '@/types/billing'

const { Text } = Typography

interface UsageStatisticsProps {
  data?: UsageStatisticsType
  skillUsage?: UsageBySkill[]
  loading?: boolean
}

const formatDuration = (ms: number) => {
  const hours = Math.floor(ms / 3600000)
  const minutes = Math.floor((ms % 3600000) / 60000)
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  }
  return `${minutes}分钟`
}

const formatNumber = (num: number) => {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(2)}M`
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`
  }
  return num.toString()
}

export default function UsageStatistics({ data, skillUsage, loading }: UsageStatisticsProps) {
  const columns = [
    {
      title: '技能名称',
      dataIndex: 'skillName',
      key: 'skillName',
    },
    {
      title: '调用次数',
      dataIndex: 'calls',
      key: 'calls',
      render: (val: number) => formatNumber(val),
    },
    {
      title: 'Tokens',
      dataIndex: 'tokens',
      key: 'tokens',
      render: (val: number) => formatNumber(val),
    },
    {
      title: '费用 (元)',
      dataIndex: 'cost',
      key: 'cost',
      render: (val: number) => `¥${val.toFixed(2)}`,
    },
    {
      title: '平均响应时间',
      dataIndex: 'avgResponseTime',
      key: 'avgResponseTime',
      render: (val: number) => `${val}ms`,
    },
    {
      title: '占比',
      dataIndex: 'percentage',
      key: 'percentage',
      render: (val: number) => (
        <Space>
          <div style={{ width: 100, height: 8, background: '#f0f0f0', borderRadius: 4 }}>
            <div
              style={{
                width: `${val}%`,
                height: '100%',
                background: '#1890ff',
                borderRadius: 4,
              }}
            />
          </div>
          <Text type="secondary">{val.toFixed(1)}%</Text>
        </Space>
      ),
    },
  ]

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card title="用量统计" loading={loading}>
        <Row gutter={[24, 24]}>
          <Col xs={24} sm={12} lg={6}>
            <Statistic
              title="总调用次数"
              value={data?.totalCalls || 0}
              prefix={<PhoneOutlined />}
              formatter={(value) => formatNumber(Number(value))}
            />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Statistic
              title="总 Tokens"
              value={data?.totalTokens || 0}
              prefix={<ThunderboltOutlined />}
              formatter={(value) => formatNumber(Number(value))}
            />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Statistic
              title="总运行时长"
              value={formatDuration(data?.totalDuration || 0)}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ fontSize: 20 }}
            />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Statistic
              title="平均每次调用费用"
              value={data?.averageCostPerCall || 0}
              precision={4}
              prefix={<DollarOutlined />}
              suffix="元"
            />
          </Col>
        </Row>
      </Card>

      <Card title="按技能分类用量" loading={loading}>
        <Table
          dataSource={skillUsage}
          columns={columns}
          rowKey="skillId"
          pagination={false}
          size="small"
        />
      </Card>
    </Space>
  )
}
