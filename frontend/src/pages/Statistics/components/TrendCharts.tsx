import { Card, Row, Col } from 'antd'
import { LineChart, BarChart } from '@/components/Charts'
import type { TrendData } from '@/types/statistics'

interface TrendChartsProps {
  trendData: TrendData[]
  loading?: boolean
}

export default function TrendCharts({ trendData, loading = false }: TrendChartsProps) {
  const downloadData = trendData.map((item) => ({
    date: item.date,
    value: item.downloads,
  }))

  const usageData = trendData.map((item) => ({
    date: item.date,
    value: item.usage,
  }))

  // 计算月度数据
  const monthlyData = trendData.reduce(
    (acc, item) => {
      const month = item.date.substring(0, 7) // YYYY-MM
      if (!acc[month]) {
        acc[month] = { downloads: 0, usage: 0 }
      }
      acc[month].downloads += item.downloads
      acc[month].usage += item.usage
      return acc
    },
    {} as Record<string, { downloads: number; usage: number }>
  )

  const barData = Object.entries(monthlyData).map(([month, data]) => ({
    name: month,
    value: data.downloads,
  }))

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={12}>
        <LineChart
          data={downloadData}
          title="下载趋势"
          xLabel="日期"
          yLabel="下载量"
          loading={loading}
          height={350}
        />
      </Col>
      <Col xs={24} lg={12}>
        <LineChart
          data={usageData}
          title="使用趋势"
          xLabel="日期"
          yLabel="使用量"
          loading={loading}
          height={350}
        />
      </Col>
      <Col xs={24}>
        <BarChart
          data={barData}
          title="月度下载量统计"
          xLabel="月份"
          yLabel="下载量"
          loading={loading}
          height={300}
        />
      </Col>
    </Row>
  )
}
