import { Card, Row, Col } from 'antd'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption } from 'echarts'
import type { ResourceUsageData } from '@/types/billing'

interface ResourceUsageChartProps {
  data?: ResourceUsageData[]
  loading?: boolean
}

export default function ResourceUsageChart({ data, loading }: ResourceUsageChartProps) {
  const cpuOption: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br />{a}: {c}%',
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
      data: data?.map((item) => item.timestamp) || [],
      axisLabel: {
        formatter: (value: string) => value.slice(5),
      },
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}%',
      },
    },
    series: [
      {
        name: 'CPU',
        type: 'line',
        smooth: true,
        data: data?.map((item) => item.cpuPercent) || [],
        areaStyle: {
          opacity: 0.4,
          color: '#1890ff',
        },
        lineStyle: {
          color: '#1890ff',
        },
        itemStyle: {
          color: '#1890ff',
        },
      },
    ],
  }

  const memoryOption: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br />{a}: {c}%',
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
      data: data?.map((item) => item.timestamp) || [],
      axisLabel: {
        formatter: (value: string) => value.slice(5),
      },
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}%',
      },
    },
    series: [
      {
        name: '内存',
        type: 'line',
        smooth: true,
        data: data?.map((item) => item.memoryPercent) || [],
        areaStyle: {
          opacity: 0.4,
          color: '#52c41a',
        },
        lineStyle: {
          color: '#52c41a',
        },
        itemStyle: {
          color: '#52c41a',
        },
      },
    ],
  }

  const networkOption: EChartsOption = {
    tooltip: {
      trigger: 'axis',
    },
    legend: {
      data: ['入站流量', '出站流量'],
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
        formatter: (value: string) => value.slice(5),
      },
    },
    yAxis: {
      type: 'value',
      name: 'MB',
    },
    series: [
      {
        name: '入站流量',
        type: 'line',
        smooth: true,
        data: data?.map((item) => item.networkIn) || [],
        lineStyle: {
          color: '#722ed1',
        },
        itemStyle: {
          color: '#722ed1',
        },
      },
      {
        name: '出站流量',
        type: 'line',
        smooth: true,
        data: data?.map((item) => item.networkOut) || [],
        lineStyle: {
          color: '#fa8c16',
        },
        itemStyle: {
          color: '#fa8c16',
        },
      },
    ],
  }

  return (
    <Card title="资源使用情况" loading={loading}>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <ReactECharts
            option={cpuOption}
            style={{ height: 200 }}
            notMerge={true}
          />
        </Col>
        <Col xs={24} lg={12}>
          <ReactECharts
            option={memoryOption}
            style={{ height: 200 }}
            notMerge={true}
          />
        </Col>
        <Col span={24}>
          <ReactECharts
            option={networkOption}
            style={{ height: 200 }}
            notMerge={true}
          />
        </Col>
      </Row>
    </Card>
  )
}
