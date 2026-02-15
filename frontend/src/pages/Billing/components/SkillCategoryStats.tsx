import { Card, Row, Col, Table } from 'antd'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption } from 'echarts'
import type { SkillCategoryStat } from '@/types/billing'

interface SkillCategoryStatsProps {
  data?: SkillCategoryStat[]
  loading?: boolean
}

const colors = ['#1890ff', '#52c41a', '#faad14', '#722ed1', '#f5222d', '#13c2c2']

export default function SkillCategoryStats({ data, loading }: SkillCategoryStatsProps) {
  const pieOption: EChartsOption = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c}元 ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'center',
    },
    series: [
      {
        name: '费用分布',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['35%', '50%'],
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
        data:
          data?.map((item, index) => ({
            value: item.cost,
            name: item.category,
            itemStyle: {
              color: colors[index % colors.length],
            },
          })) || [],
      },
    ],
  }

  const columns = [
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
    },
    {
      title: '调用次数',
      dataIndex: 'calls',
      key: 'calls',
      render: (val: number) => val.toLocaleString(),
    },
    {
      title: '费用 (元)',
      dataIndex: 'cost',
      key: 'cost',
      render: (val: number) => `¥${val.toFixed(2)}`,
    },
    {
      title: '占比',
      dataIndex: 'percentage',
      key: 'percentage',
      render: (val: number) => `${val.toFixed(1)}%`,
    },
  ]

  return (
    <Card title="技能分类统计" loading={loading}>
      <Row gutter={24}>
        <Col xs={24} lg={10}>
          <ReactECharts
            option={pieOption}
            style={{ height: 300 }}
            notMerge={true}
          />
        </Col>
        <Col xs={24} lg={14}>
          <Table
            dataSource={data}
            columns={columns}
            rowKey="category"
            pagination={false}
            size="small"
          />
        </Col>
      </Row>
    </Card>
  )
}
