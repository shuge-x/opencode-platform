import { Card, Row, Col } from 'antd'
import { PieChart, BarChart } from '@/components/Charts'
import type { CategoryDistribution, RatingDistribution } from '@/types/statistics'

interface DistributionChartsProps {
  categoryData: CategoryDistribution[]
  ratingData: RatingDistribution[]
  loading?: boolean
}

export default function DistributionCharts({
  categoryData,
  ratingData,
  loading = false,
}: DistributionChartsProps) {
  const categoryChartData = categoryData.map((item) => ({
    name: item.category,
    value: item.count,
  }))

  const ratingChartData = ratingData.map((item) => ({
    name: `${item.rating} 星`,
    value: item.count,
  }))

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={14}>
        <PieChart
          data={categoryChartData}
          title="技能分类分布"
          loading={loading}
          height={350}
        />
      </Col>
      <Col xs={24} lg={10}>
        <BarChart
          data={ratingChartData}
          title="评分分布"
          xLabel="评分"
          yLabel="技能数"
          loading={loading}
          height={350}
        />
      </Col>
    </Row>
  )
}
