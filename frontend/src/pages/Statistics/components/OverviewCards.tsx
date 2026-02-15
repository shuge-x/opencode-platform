import { Card, Statistic, Row, Col } from 'antd'
import {
  AppstoreOutlined,
  DownloadOutlined,
  UserOutlined,
  RiseOutlined,
} from '@ant-design/icons'

interface OverviewCardsProps {
  totalSkills: number
  totalDownloads: number
  totalUsers: number
  activeUsersToday: number
  growthRate: number
  loading?: boolean
}

export default function OverviewCards({
  totalSkills,
  totalDownloads,
  totalUsers,
  activeUsersToday,
  growthRate,
  loading = false,
}: OverviewCardsProps) {
  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} lg={6}>
        <Card loading={loading}>
          <Statistic
            title="总技能数"
            value={totalSkills}
            prefix={<AppstoreOutlined />}
            valueStyle={{ color: '#1890ff' }}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card loading={loading}>
          <Statistic
            title="总下载量"
            value={totalDownloads}
            prefix={<DownloadOutlined />}
            valueStyle={{ color: '#52c41a' }}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card loading={loading}>
          <Statistic
            title="总用户数"
            value={totalUsers}
            prefix={<UserOutlined />}
            valueStyle={{ color: '#722ed1' }}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card loading={loading}>
          <Statistic
            title="今日活跃用户"
            value={activeUsersToday}
            prefix={<RiseOutlined />}
            valueStyle={{ color: '#eb2f96' }}
            suffix={
              <span style={{ fontSize: 14, color: growthRate >= 0 ? '#52c41a' : '#f5222d' }}>
                {growthRate >= 0 ? '+' : ''}
                {growthRate}%
              </span>
            }
          />
        </Card>
      </Col>
    </Row>
  )
}
