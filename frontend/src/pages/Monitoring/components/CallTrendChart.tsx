import ReactECharts from 'echarts-for-react'
import { Card, Empty } from 'antd'
import type { CallTrendData } from '@/types/monitoring'

interface CallTrendChartProps {
  data?: CallTrendData[]
  loading?: boolean
}

export default function CallTrendChart({ data, loading = false }: CallTrendChartProps) {
  const getOption = () => {
    if (!data || data.length === 0) {
      return {}
    }

    const timestamps = data.map((item) => item.timestamp)
    const calls = data.map((item) => item.calls)
    const errors = data.map((item) => item.errors)

    return {
      title: {
        text: '调用量趋势',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
      },
      legend: {
        data: ['调用次数', '错误次数'],
        bottom: 0,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: timestamps,
      },
      yAxis: {
        type: 'value',
      },
      series: [
        {
          name: '调用次数',
          type: 'line',
          smooth: true,
          data: calls,
          itemStyle: {
            color: '#1890ff',
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
                { offset: 1, color: 'rgba(24, 144, 255, 0.05)' },
              ],
            },
          },
        },
        {
          name: '错误次数',
          type: 'line',
          smooth: true,
          data: errors,
          itemStyle: {
            color: '#f5222d',
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
