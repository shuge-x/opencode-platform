import { Table, Card, Tabs, Tag, Rate, Space } from 'antd'
import type { TabsProps } from 'antd'
import { FireOutlined, ClockCircleOutlined, StarOutlined } from '@ant-design/icons'
import { useState } from 'react'
import type { SkillRanking } from '@/types/statistics'

interface SkillRankingTableProps {
  popularSkills: SkillRanking[]
  latestSkills: SkillRanking[]
  topRatedSkills: SkillRanking[]
  loading?: boolean
  onLoadMore?: (type: 'popular' | 'latest' | 'topRated') => void
}

export default function SkillRankingTable({
  popularSkills,
  latestSkills,
  topRatedSkills,
  loading = false,
}: SkillRankingTableProps) {
  const [activeTab, setActiveTab] = useState('popular')

  const columns = [
    {
      title: '排名',
      key: 'rank',
      width: 70,
      render: (_: any, __: any, index: number) => (
        <Tag color={index < 3 ? 'gold' : 'default'}>#{index + 1}</Tag>
      ),
    },
    {
      title: '技能名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <a>{text}</a>,
    },
    {
      title: '作者',
      dataIndex: 'author',
      key: 'author',
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => <Tag>{category}</Tag>,
    },
    {
      title: '下载量',
      dataIndex: 'downloads',
      key: 'downloads',
      sorter: (a: SkillRanking, b: SkillRanking) => a.downloads - b.downloads,
    },
    {
      title: '评分',
      dataIndex: 'rating',
      key: 'rating',
      sorter: (a: SkillRanking, b: SkillRanking) => a.rating - b.rating,
      render: (rating: number) => <Rate disabled defaultValue={rating} allowHalf />,
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      sorter: (a: SkillRanking, b: SkillRanking) =>
        new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime(),
    },
  ]

  const items: TabsProps['items'] = [
    {
      key: 'popular',
      label: (
        <Space>
          <FireOutlined />
          热门技能
        </Space>
      ),
      children: (
        <Table
          columns={columns}
          dataSource={popularSkills}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          loading={loading}
        />
      ),
    },
    {
      key: 'latest',
      label: (
        <Space>
          <ClockCircleOutlined />
          最新技能
        </Space>
      ),
      children: (
        <Table
          columns={columns}
          dataSource={latestSkills}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          loading={loading}
        />
      ),
    },
    {
      key: 'topRated',
      label: (
        <Space>
          <StarOutlined />
          高评分技能
        </Space>
      ),
      children: (
        <Table
          columns={columns}
          dataSource={topRatedSkills}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          loading={loading}
        />
      ),
    },
  ]

  return (
    <Card>
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={items} />
    </Card>
  )
}
