import { Card, Row, Col, Statistic } from 'antd'
import { DashboardOutlined } from '@ant-design/icons'
import type { PerformanceMetrics } from '@/types/monitoring'

interface PerformanceMetricsDisplayProps {
  data?: PerformanceMetrics
  loading?: boolean
}

export default function PerformanceMetricsDisplay({
  data,
  loading = false,
}: PerformanceMetricsDisplayProps) {
  return (
    <Card title="性能指标" loading={loading} extra={<DashboardOutlined />}>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={8}>
          <Statistic
            title="P50 响应时间"
            value={data?.p50 || 0}
            suffix="ms"
            valueStyle={{ color: '#52c41a' }}
          />
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Statistic
            title="P95 响应时间"
            value={data?.p95 || 0}
            suffix="ms"
            valueStyle={{ color: '#1890ff' }}
          />
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Statistic
            title="P99 响应时间"
            value={data?.p99 || 0}
            suffix="ms"
            valueStyle={{ color: '#f5222d' }}
          />
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Statistic title="最小响应时间" value={data?.min || 0} suffix="ms" />
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Statistic title="最大响应时间" value={data?.max || 0} suffix="ms" />
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Statistic title="平均响应时间" value={data?.avg || 0} suffix="ms" />
        </Col>
      </Row>
    </Card>
  )
}
