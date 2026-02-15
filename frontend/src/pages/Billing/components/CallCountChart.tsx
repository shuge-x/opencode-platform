import { Card } from 'antd'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption } from 'echarts'
import type { CallTrendData } from '@/types/billing'

interface CallCountChartProps {
  data?: CallTrendData[]
  loading?: boolean
}

export default function CallCountChart({ data, loading }: CallCountChartProps) {
  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
    },
    legend: {
      data: ['总调用', '成功', '错误'],
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
      data: data?.map((item) => item.timestamp) || [],
      axisLabel: {
        formatter: (value: string) => value.slice(5), // 只显示 MM-DD
      },
    },
    yAxis: {
      type: 'value',
      name: '调用次数',
    },
    series: [
      {
        name: '总调用',
        type: 'line',
        smooth: true,
        data: data?.map((item) => item.calls) || [],
        areaStyle: {
          opacity: 0.3,
        },
        lineStyle: {
          width: 2,
        },
        itemStyle: {
          color: '#1890ff',
        },
      },
      {
        name: '成功',
        type: 'line',
        smooth: true,
        data: data?.map((item) => item.success) || [],
        lineStyle: {
          width: 2,
          type: 'dashed',
        },
        itemStyle: {
          color: '#52c41a',
        },
      },
      {
        name: '错误',
        type: 'line',
        smooth: true,
        data: data?.map((item) => item.errors) || [],
        lineStyle: {
          width: 2,
        },
        itemStyle: {
          color: '#f5222d',
        },
      },
    ],
  }

  return (
    <Card title="调用次数趋势" loading={loading}>
      <ReactECharts
        option={option}
        style={{ height: 300 }}
        notMerge={true}
        lazyUpdate={true}
      />
    </Card>
  )
}
