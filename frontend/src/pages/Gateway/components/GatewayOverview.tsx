import React from 'react'
import { Card, Row, Col, Statistic, Progress, Spin, Alert } from 'antd'
import {
  ApiOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  StopOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { gatewayStatsApi } from '@/api/gateway'

export default function GatewayOverview() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['gateway-stats'],
    queryFn: gatewayStatsApi.get,
    refetchInterval: 30000, // 每30秒刷新
  })

  if (isLoading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Alert
        message="加载失败"
        description="无法获取网关统计信息"
        type="error"
        showIcon
      />
    )
  }

  return (
    <Card title="网关概览">
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总路由数"
              value={stats?.totalRoutes || 0}
              prefix={<ApiOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ marginTop: 8 }}>
              <span style={{ color: '#52c41a' }}>
                {stats?.activeRoutes || 0} 已启用
              </span>
              <span style={{ color: '#999', marginLeft: 8 }}>
                {((stats?.totalRoutes || 0) - (stats?.activeRoutes || 0))} 已禁用
              </span>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总请求数"
              value={stats?.totalRequests || 0}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="成功率"
              value={stats?.successRate || 0}
              precision={2}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: stats?.successRate && stats.successRate > 95 ? '#52c41a' : '#faad14' }}
            />
            <Progress
              percent={stats?.successRate || 0}
              showInfo={false}
              strokeColor={stats?.successRate && stats.successRate > 95 ? '#52c41a' : '#faad14'}
              size="small"
              style={{ marginTop: 8 }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均延迟"
              value={stats?.avgLatency || 0}
              precision={2}
              suffix="ms"
              prefix={<ClockCircleOutlined />}
              valueStyle={{
                color:
                  (stats?.avgLatency || 0) < 100
                    ? '#52c41a'
                    : (stats?.avgLatency || 0) < 500
                      ? '#faad14'
                      : '#f5222d',
              }}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
              {(stats?.avgLatency || 0) < 100
                ? '响应良好'
                : (stats?.avgLatency || 0) < 500
                  ? '响应一般'
                  : '响应较慢'}
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="限流拦截"
              value={stats?.rateLimitedRequests || 0}
              prefix={<StopOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
              被限流策略拦截的请求数
            </div>
          </Card>
        </Col>
      </Row>
    </Card>
  )
}
