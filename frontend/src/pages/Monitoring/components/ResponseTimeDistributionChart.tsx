import ReactECharts from 'echarts-for-react'
import { Card, Empty } from 'antd'
import type { ResponseTimeDistribution } from '@/types/monitoring'

interface ResponseTimeDistributionChartProps {
  data?: ResponseTimeDistribution[]
  loading?: boolean
}

export default function ResponseTimeDistributionChart({
  data,
  loading = false,
}: ResponseTimeDistributionChartProps) {
  const getOption = () => {
    if (!data || data.length === 0) {
      return {}
    }

    const ranges = data.map((item) => item.range)
    const counts = data.map((item) => item.count)

    return {
      title: {
        text: '响应时间分布',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
        formatter: (params: any) => {
          const item = params[0]
          const percentage = data[item.dataIndex].percentage
          return `${item.name}<br/>${item.seriesName}: ${item.value}<br/>占比: ${percentage}%`
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
        data: ranges,
        axisLabel: {
          rotate: 45,
        },
      },
      yAxis: {
        type: 'value',
        name: '次数',
      },
      series: [
        {
          name: '响应次数',
          type: 'bar',
          data: counts,
          itemStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: '#52c41a' },
                { offset: 1, color: '#1890ff' },
              ],
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
