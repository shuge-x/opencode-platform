import ReactECharts from 'echarts-for-react'
import { Card } from 'antd'
import type { EChartsOption } from 'echarts'

interface LineChartProps {
  data: Array<{ date: string; value: number }>
  title?: string
  xLabel?: string
  yLabel?: string
  loading?: boolean
  height?: number
}

export default function LineChart({
  data,
  title,
  xLabel = '日期',
  yLabel = '数量',
  loading = false,
  height = 300,
}: LineChartProps) {
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
        type: 'cross',
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
      data: data.map((item) => item.date),
      name: xLabel,
      nameLocation: 'middle',
      nameGap: 30,
    },
    yAxis: {
      type: 'value',
      name: yLabel,
      nameLocation: 'middle',
      nameGap: 40,
    },
    series: [
      {
        name: yLabel,
        type: 'line',
        smooth: true,
        data: data.map((item) => item.value),
        areaStyle: {
          opacity: 0.3,
        },
        emphasis: {
          focus: 'series',
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
