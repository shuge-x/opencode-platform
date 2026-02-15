import { Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import type { TopSkillRanking } from '@/types/monitoring'

interface TopSkillsTableProps {
  data?: TopSkillRanking[]
  loading?: boolean
}

export default function TopSkillsTable({ data, loading = false }: TopSkillsTableProps) {
  const columns: ColumnsType<TopSkillRanking> = [
    {
      title: '排名',
      key: 'rank',
      width: 70,
      render: (_, __, index) => (
        <Tag color={index < 3 ? 'gold' : 'default'}>
          {index + 1}
        </Tag>
      ),
    },
    {
      title: '技能名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '调用次数',
      dataIndex: 'calls',
      key: 'calls',
      sorter: (a, b) => a.calls - b.calls,
    },
    {
      title: '平均响应时间',
      dataIndex: 'avgResponseTime',
      key: 'avgResponseTime',
      render: (value: number) => `${value}ms`,
      sorter: (a, b) => a.avgResponseTime - b.avgResponseTime,
    },
    {
      title: '错误率',
      dataIndex: 'errorRate',
      key: 'errorRate',
      render: (value: number) => (
        <Tag color={value > 5 ? 'red' : value > 2 ? 'orange' : 'green'}>
          {value.toFixed(2)}%
        </Tag>
      ),
      sorter: (a, b) => a.errorRate - b.errorRate,
    },
    {
      title: '成功率',
      dataIndex: 'successRate',
      key: 'successRate',
      render: (value: number) => (
        <Tag color={value >= 95 ? 'green' : value >= 90 ? 'orange' : 'red'}>
          {value.toFixed(2)}%
        </Tag>
      ),
      sorter: (a, b) => a.successRate - b.successRate,
    },
  ]

  return (
    <Table
      columns={columns}
      dataSource={data}
      loading={loading}
      rowKey="id"
      pagination={{
        pageSize: 10,
        showSizeChanger: true,
        showTotal: (total) => `共 ${total} 条`,
      }}
    />
  )
}
