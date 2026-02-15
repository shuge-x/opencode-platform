import ReactECharts from 'echarts-for-react'
import { Card } from 'antd'
import type { EChartsOption } from 'echarts'

interface BarChartProps {
  data: Array<{ name: string; value: number }>
  title?: string
  xLabel?: string
  yLabel?: string
  loading?: boolean
  height?: number
  horizontal?: boolean
}

export default function BarChart({
  data,
  title,
  xLabel,
  yLabel,
  loading = false,
  height = 300,
  horizontal = false,
}: BarChartProps) {
  const option: EChartsOption = {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal',
      },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: horizontal
      ? { type: 'value', name: xLabel }
      : {
          type: 'category',
          data: data.map((item) => item.name),
          name: xLabel,
          nameLocation: 'middle',
          nameGap: 30,
          axisLabel: {
            rotate: data.length > 6 ? 45 : 0,
          },
        },
    yAxis: horizontal
      ? {
          type: 'category',
          data: data.map((item) => item.name),
          name: yLabel,
        }
      : { type: 'value', name: yLabel, nameLocation: 'middle', nameGap: 40 },
    series: [
      {
        name: yLabel || '数量',
        type: 'bar',
        data: data.map((item) => item.value),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      },
    ],
  }

  return (
    <Card loading={loading}>
      <ReactECharts
        option={option}
        style={{ height: `${height}px`, width: '100%' }}
        opts={{ renderer: 'svg' }}
        lazyUpdate
      />
    </Card>
  )
}
