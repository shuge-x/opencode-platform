import { Card, Row, Col, Statistic, Progress, Typography, Space } from 'antd'
import {
  DollarOutlined,
  WalletOutlined,
  RiseOutlined,
  PieChartOutlined,
} from '@ant-design/icons'
import type { CostOverview as CostOverviewType } from '@/types/billing'

const { Text } = Typography

interface CostOverviewProps {
  data?: CostOverviewType
  loading?: boolean
}

export default function CostOverview({ data, loading }: CostOverviewProps) {
  if (!data) {
    return null
  }

  const getBudgetColor = (percent: number) => {
    if (percent < 50) return '#52c41a'
    if (percent < 80) return '#faad14'
    return '#f5222d'
  }

  return (
    <Card title="费用总览" loading={loading}>
      <Row gutter={[24, 24]}>
        <Col xs={24} sm={12} lg={6}>
          <Statistic
            title="账户余额"
            value={data.currentBalance}
            precision={2}
            prefix={<WalletOutlined />}
            suffix="元"
            valueStyle={{ color: '#1890ff' }}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Statistic
            title="本月消费"
            value={data.monthlySpend}
            precision={2}
            prefix={<DollarOutlined />}
            suffix="元"
            valueStyle={{ color: '#52c41a' }}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Statistic
            title="本月预算"
            value={data.monthlyBudget}
            precision={2}
            prefix={<PieChartOutlined />}
            suffix="元"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Statistic
            title="预计本月消费"
            value={data.projectedSpend}
            precision={2}
            prefix={<RiseOutlined />}
            suffix="元"
            valueStyle={{ color: '#722ed1' }}
          />
        </Col>
      </Row>

      <div style={{ marginTop: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <Text>预算使用率</Text>
            <Text type="secondary">{data.budgetUsagePercent.toFixed(1)}%</Text>
          </div>
          <Progress
            percent={data.budgetUsagePercent}
            strokeColor={getBudgetColor(data.budgetUsagePercent)}
            showInfo={false}
          />
        </Space>
      </div>
    </Card>
  )
}
