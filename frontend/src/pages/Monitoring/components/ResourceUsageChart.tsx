import ReactECharts from 'echarts-for-react'
import { Card, Empty } from 'antd'
import type { ResourceUsage } from '@/types/monitoring'

interface ResourceUsageChartProps {
  data?: ResourceUsage[]
  loading?: boolean
}

export default function ResourceUsageChart({ data, loading = false }: ResourceUsageChartProps) {
  const getOption = () => {
    if (!data || data.length === 0) {
      return {}
    }

    const timestamps = data.map((item) => item.timestamp)
    const cpuUsage = data.map((item) => item.cpuUsage)
    const memoryUsage = data.map((item) => item.memoryUsage)

    return {
      title: {
        text: '资源使用率',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
      },
      legend: {
        data: ['CPU 使用率', '内存使用率'],
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
        name: '使用率 (%)',
        max: 100,
      },
      series: [
        {
          name: 'CPU 使用率',
          type: 'line',
          smooth: true,
          data: cpuUsage,
          itemStyle: {
            color: '#1890ff',
          },
        },
        {
          name: '内存使用率',
          type: 'line',
          smooth: true,
          data: memoryUsage,
          itemStyle: {
            color: '#52c41a',
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
