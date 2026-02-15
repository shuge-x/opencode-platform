import ReactECharts from 'echarts-for-react'
import { Card } from 'antd'
import type { EChartsOption } from 'echarts'

interface PieChartProps {
  data: Array<{ name: string; value: number }>
  title?: string
  loading?: boolean
  height?: number
  showLegend?: boolean
}

export default function PieChart({
  data,
  title,
  loading = false,
  height = 300,
  showLegend = true,
}: PieChartProps) {
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
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)',
    },
    legend: showLegend
      ? {
          orient: 'vertical',
          left: 'left',
          top: 'middle',
        }
      : undefined,
    series: [
      {
        name: title || '分类',
        type: 'pie',
        radius: ['40%', '70%'],
        center: showLegend ? ['60%', '50%'] : ['50%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: false,
          position: 'center',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold',
          },
        },
        labelLine: {
          show: false,
        },
        data: data.map((item) => ({
          name: item.name,
          value: item.value,
        })),
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
