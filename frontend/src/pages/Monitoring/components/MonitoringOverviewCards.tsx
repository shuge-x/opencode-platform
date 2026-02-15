import { Card, Statistic, Row, Col, Spin } from 'antd'
import {
  ThunderboltOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  RocketOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import type { MonitoringOverview } from '@/types/monitoring'

interface MonitoringOverviewCardsProps {
  data?: MonitoringOverview
  loading?: boolean
}

export default function MonitoringOverviewCards({
  data,
  loading = false,
}: MonitoringOverviewCardsProps) {
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="总调用数"
            value={data?.totalCalls || 0}
            prefix={<ThunderboltOutlined />}
            valueStyle={{ color: '#1890ff' }}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="平均响应时间"
            value={data?.avgResponseTime || 0}
            suffix="ms"
            prefix={<ClockCircleOutlined />}
            valueStyle={{ color: '#52c41a' }}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="错误率"
            value={data?.errorRate || 0}
            suffix="%"
            prefix={<WarningOutlined />}
            valueStyle={{ color: data?.errorRate && data.errorRate > 5 ? '#f5222d' : '#52c41a' }}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="吞吐量"
            value={data?.throughput || 0}
            suffix="req/s"
            prefix={<RocketOutlined />}
            valueStyle={{ color: '#722ed1' }}
          />
        </Card>
      </Col>
    </Row>
  )
}
