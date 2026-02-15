import { Card } from 'antd'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption } from 'echarts'
import type { CostTrendData } from '@/types/billing'

interface CostTrendChartProps {
  data?: CostTrendData[]
  loading?: boolean
}

export default function CostTrendChart({ data, loading }: CostTrendChartProps) {
  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
      formatter: (params: any) => {
        const date = params[0].axisValue
        let result = `<div style="font-weight: bold">${date}</div>`
        params.forEach((item: any) => {
          if (item.seriesName === '费用') {
            result += `<div>${item.marker} ${item.seriesName}: ¥${item.value?.toFixed(2)}</div>`
          } else {
            result += `<div>${item.marker} ${item.seriesName}: ${item.value?.toLocaleString()}</div>`
          }
        })
        return result
      },
    },
    legend: {
      data: ['费用', '调用次数', 'Tokens'],
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
      data: data?.map((item) => item.date) || [],
      axisLabel: {
        formatter: (value: string) => value.slice(5),
      },
    },
    yAxis: [
      {
        type: 'value',
        name: '费用 (元)',
        position: 'left',
        axisLabel: {
          formatter: '¥{value}',
        },
      },
      {
        type: 'value',
        name: '数量',
        position: 'right',
      },
    ],
    series: [
      {
        name: '费用',
        type: 'line',
        smooth: true,
        data: data?.map((item) => item.cost) || [],
        yAxisIndex: 0,
        areaStyle: {
          opacity: 0.3,
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#722ed1' },
              { offset: 1, color: '#f0f0f0' },
            ],
          },
        },
        lineStyle: {
          width: 3,
          color: '#722ed1',
        },
        itemStyle: {
          color: '#722ed1',
        },
      },
      {
        name: '调用次数',
        type: 'bar',
        data: data?.map((item) => item.calls) || [],
        yAxisIndex: 1,
        barWidth: '30%',
        itemStyle: {
          color: '#1890ff',
          opacity: 0.6,
        },
      },
      {
        name: 'Tokens',
        type: 'line',
        smooth: true,
        data: data?.map((item) => item.tokens) || [],
        yAxisIndex: 1,
        lineStyle: {
          type: 'dashed',
          color: '#52c41a',
        },
        itemStyle: {
          color: '#52c41a',
        },
      },
    ],
  }

  return (
    <Card title="费用趋势" loading={loading}>
      <ReactECharts
        option={option}
        style={{ height: 350 }}
        notMerge={true}
        lazyUpdate={true}
      />
    </Card>
  )
}
