import ReactECharts from 'echarts-for-react'
import { Card, Empty } from 'antd'
import type { CallTrendData } from '@/types/monitoring'

interface ErrorRateChartProps {
  data?: CallTrendData[]
  loading?: boolean
}

export default function ErrorRateChart({ data, loading = false }: ErrorRateChartProps) {
  const getOption = () => {
    if (!data || data.length === 0) {
      return {}
    }

    const timestamps = data.map((item) => item.timestamp)
    const errorRates = data.map((item) => {
      const rate = item.calls > 0 ? (item.errors / item.calls) * 100 : 0
      return rate.toFixed(2)
    })

    return {
      title: {
        text: '错误率趋势',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const item = params[0]
          return `${item.name}<br/>错误率: ${item.value}%`
        },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: timestamps,
      },
      yAxis: {
        type: 'value',
        name: '错误率 (%)',
        max: 100,
      },
      series: [
        {
          name: '错误率',
          type: 'line',
          smooth: true,
          data: errorRates,
          itemStyle: {
            color: '#f5222d',
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(245, 34, 45, 0.3)' },
                { offset: 1, color: 'rgba(245, 34, 45, 0.05)' },
              ],
            },
          },
          markLine: {
            data: [{ yAxis: 5, name: '警戒线', label: { formatter: '警戒线 5%' } }],
            lineStyle: {
              color: '#ff4d4f',
              type: 'dashed',
            },
          },
        },
      ],
    }
  }

  return (
    <Card loading={loading}>
      {data && data.length > 0 ? (
        <ReactECharts option={getOption()} style={{ height: 400 }} />
      ) : (
        <Empty description="暂无数据" />
      )}
    </Card>
  )
}
