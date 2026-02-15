import { useState } from 'react'
import { Card, Tabs, Row, Col, Space, Typography } from 'antd'
import { DashboardOutlined, AlertOutlined } from '@ant-design/icons'
import MonitoringOverviewCards from './components/MonitoringOverviewCards'
import CallTrendChart from './components/CallTrendChart'
import ResponseTimeDistributionChart from './components/ResponseTimeDistributionChart'
import ErrorRateChart from './components/ErrorRateChart'
import PerformanceMetricsDisplay from './components/PerformanceMetricsDisplay'
import ResourceUsageChart from './components/ResourceUsageChart'
import TopSkillsTable from './components/TopSkillsTable'
import ErrorList from './components/ErrorList'
import ErrorFilter from './components/ErrorFilter'
import TimeRangeSelector from './components/TimeRangeSelector'
import {
  useMonitoringOverview,
  useCallTrends,
  useResponseTimeDistribution,
  usePerformanceMetrics,
  useResourceUsage,
  useTopSkillRankings,
  useErrors,
} from '@/hooks/useMonitoring'
import type { MonitoringQueryParams } from '@/types/monitoring'

const { Title } = Typography

export default function MonitoringDashboard() {
  const [queryParams, setQueryParams] = useState<MonitoringQueryParams>({
    timeRange: '24h',
  })

  const { data: overviewData, isLoading: overviewLoading } = useMonitoringOverview(queryParams)
  const { data: trendData, isLoading: trendLoading } = useCallTrends(queryParams)
  const { data: distributionData, isLoading: distributionLoading } = useResponseTimeDistribution(queryParams)
  const { data: performanceData, isLoading: performanceLoading } = usePerformanceMetrics(queryParams)
  const { data: resourceData, isLoading: resourceLoading } = useResourceUsage(queryParams)
  const { data: rankingsData, isLoading: rankingsLoading } = useTopSkillRankings(queryParams)
  const { data: errorsData, isLoading: errorsLoading } = useErrors(queryParams)

  const handleTimeRangeChange = (value: any) => {
    setQueryParams((prev) => ({
      ...prev,
      ...value,
    }))
  }

  const tabItems = [
    {
      key: 'dashboard',
      label: (
        <span>
          <DashboardOutlined />
          监控仪表板
        </span>
      ),
      children: (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <MonitoringOverviewCards data={overviewData} loading={overviewLoading} />

          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <CallTrendChart data={trendData} loading={trendLoading} />
            </Col>
            <Col xs={24} lg={12}>
              <ErrorRateChart data={trendData} loading={trendLoading} />
            </Col>
          </Row>

          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <ResponseTimeDistributionChart data={distributionData} loading={distributionLoading} />
            </Col>
            <Col xs={24} lg={12}>
              <PerformanceMetricsDisplay data={performanceData} loading={performanceLoading} />
            </Col>
          </Row>

          <ResourceUsageChart data={resourceData} loading={resourceLoading} />

          <Card title="Top 技能排行">
            <TopSkillsTable data={rankingsData} loading={rankingsLoading} />
          </Card>
        </Space>
      ),
    },
    {
      key: 'errors',
      label: (
        <span>
          <AlertOutlined />
          错误追踪
        </span>
      ),
      children: (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <ErrorFilter
            onFilter={(filters) => {
              setQueryParams((prev) => ({
                ...prev,
                ...filters,
              }))
            }}
            loading={errorsLoading}
          />
          <Card>
            <ErrorList
              data={errorsData?.data}
              total={errorsData?.total}
              loading={errorsLoading}
              onPageChange={(page, pageSize) => {
                setQueryParams((prev) => ({
                  ...prev,
                  offset: (page - 1) * pageSize,
                  limit: pageSize,
                }))
              }}
            />
          </Card>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={2} style={{ margin: 0 }}>
            技能调用监控
          </Title>
          <TimeRangeSelector onChange={handleTimeRangeChange} />
        </div>

        <Tabs defaultActiveKey="dashboard" items={tabItems} />
      </Space>
    </div>
  )
}
