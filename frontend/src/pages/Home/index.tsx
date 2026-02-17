import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Typography,
  Card,
  Row,
  Col,
  Button,
  Statistic,
  List,
  Avatar,
  Empty,
  Space,
  Tag,
  Skeleton,
} from 'antd'
import {
  PlusOutlined,
  ThunderboltOutlined,
  PartitionOutlined,
  MessageOutlined,
  AppstoreOutlined,
  RocketOutlined,
  ClockCircleOutlined,
  DashboardOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '@/stores/authStore'
import { useSessionStore } from '@/stores/sessionStore'
import { useSkillStore } from '@/stores/skillStore'
import { useWorkflowStore } from '@/stores/workflowStore'
import './Home.css'

const { Title, Text, Paragraph } = Typography

// 模拟统计数据
interface DashboardStats {
  todaySessions: number
  skillExecutions: number
  workflowRuns: number
  totalSkills: number
}

// 模拟最近使用数据
interface RecentItem {
  id: string
  name: string
  description?: string
  updatedAt: string
  type?: 'session' | 'skill' | 'workflow'
}

export default function HomePage() {
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)
  const sessions = useSessionStore((state) => state.sessions)
  const skills = useSkillStore((state) => state.installedSkills)
  const { currentWorkflow } = useWorkflowStore()
  
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<DashboardStats>({
    todaySessions: 0,
    skillExecutions: 0,
    workflowRuns: 0,
    totalSkills: 0,
  })
  
  // 模拟最近使用数据
  const [recentSessions] = useState<RecentItem[]>([
    { id: '1', name: '代码审查对话', updatedAt: '2小时前' },
    { id: '2', name: 'API设计讨论', updatedAt: '5小时前' },
    { id: '3', name: 'Bug分析会话', updatedAt: '昨天' },
  ])
  
  const [recentSkills] = useState<RecentItem[]>([
    { id: '1', name: '代码生成器', description: '智能生成高质量代码', updatedAt: '1小时前' },
    { id: '2', name: '数据分析', description: '数据可视化工具', updatedAt: '3小时前' },
    { id: '3', name: '文档助手', description: '自动生成文档', updatedAt: '昨天' },
  ])
  
  const [recentWorkflows] = useState<RecentItem[]>([
    { id: '1', name: 'CI/CD 部署流程', description: '自动化部署工作流', updatedAt: '4小时前' },
    { id: '2', name: '数据同步任务', description: '定时数据同步', updatedAt: '昨天' },
    { id: '3', name: '报告生成流程', description: '周报自动生成', updatedAt: '2天前' },
  ])

  useEffect(() => {
    // 模拟加载统计数据
    const timer = setTimeout(() => {
      setStats({
        todaySessions: 12,
        skillExecutions: 48,
        workflowRuns: 7,
        totalSkills: skills.length || 8,
      })
      setLoading(false)
    }, 500)
    
    return () => clearTimeout(timer)
  }, [skills.length])

  // 获取当前时间问候语
  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 6) return '夜深了'
    if (hour < 9) return '早上好'
    if (hour < 12) return '上午好'
    if (hour < 14) return '中午好'
    if (hour < 18) return '下午好'
    if (hour < 22) return '晚上好'
    return '夜深了'
  }

  // 快速操作按钮
  const QuickActions = () => (
    <Card className="quick-actions-card" bordered={false}>
      <div className="quick-actions-title">快速操作</div>
      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Button
            type="primary"
            icon={<MessageOutlined />}
            size="large"
            block
            className="quick-action-btn"
            onClick={() => navigate('/chat/new')}
          >
            新建会话
          </Button>
        </Col>
        <Col span={8}>
          <Button
            icon={<AppstoreOutlined />}
            size="large"
            block
            className="quick-action-btn secondary"
            onClick={() => navigate('/skills')}
          >
            创建技能
          </Button>
        </Col>
        <Col span={8}>
          <Button
            icon={<PartitionOutlined />}
            size="large"
            block
            className="quick-action-btn secondary"
            onClick={() => navigate('/workflows')}
          >
            创建工作流
          </Button>
        </Col>
      </Row>
    </Card>
  )

  // 统计卡片
  const StatsCards = () => (
    <Row gutter={[16, 16]}>
      <Col xs={12} sm={6}>
        <Card className="stats-card" bordered={false}>
          <Statistic
            title="今日会话"
            value={stats.todaySessions}
            prefix={<MessageOutlined />}
            valueStyle={{ color: '#1890ff' }}
          />
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card className="stats-card" bordered={false}>
          <Statistic
            title="技能执行"
            value={stats.skillExecutions}
            prefix={<ThunderboltOutlined />}
            valueStyle={{ color: '#52c41a' }}
          />
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card className="stats-card" bordered={false}>
          <Statistic
            title="工作流运行"
            value={stats.workflowRuns}
            prefix={<PartitionOutlined />}
            valueStyle={{ color: '#722ed1' }}
          />
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card className="stats-card" bordered={false}>
          <Statistic
            title="已安装技能"
            value={stats.totalSkills}
            prefix={<AppstoreOutlined />}
            valueStyle={{ color: '#fa8c16' }}
          />
        </Card>
      </Col>
    </Row>
  )

  // 最近使用列表组件
  const RecentList = ({
    title,
    icon,
    items,
    type,
    emptyText,
    viewAllPath,
  }: {
    title: string
    icon: React.ReactNode
    items: RecentItem[]
    type: 'session' | 'skill' | 'workflow'
    emptyText: string
    viewAllPath: string
  }) => (
    <Card
      className="recent-list-card"
      bordered={false}
      title={
        <Space>
          {icon}
          <span>{title}</span>
        </Space>
      }
      extra={
        <Button type="link" onClick={() => navigate(viewAllPath)}>
          查看全部
        </Button>
      }
    >
      {items.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={emptyText}
          className="empty-state"
        />
      ) : (
        <List
          dataSource={items}
          renderItem={(item) => (
            <List.Item
              className="recent-item"
              onClick={() => {
                if (type === 'session') navigate(`/chat/${item.id}`)
                else if (type === 'skill') navigate(`/skills/${item.id}`)
                else navigate(`/workflows/${item.id}`)
              }}
            >
              <List.Item.Meta
                avatar={
                  <Avatar
                    className={`recent-item-avatar ${type}`}
                    icon={
                      type === 'session' ? (
                        <MessageOutlined />
                      ) : type === 'skill' ? (
                        <AppstoreOutlined />
                      ) : (
                        <PartitionOutlined />
                      )
                    }
                  />
                }
                title={item.name}
                description={item.description || '暂无描述'}
              />
              <Text type="secondary" className="recent-item-time">
                <ClockCircleOutlined /> {item.updatedAt}
              </Text>
            </List.Item>
          )}
        />
      )}
    </Card>
  )

  return (
    <div className="home-page">
      {/* 欢迎卡片 */}
      <Card className="welcome-card" bordered={false}>
        <Row align="middle" gutter={[24, 16]}>
          <Col flex="auto">
            <div className="welcome-content">
              <Title level={3} className="welcome-title">
                {getGreeting()}，{user?.username || '用户'} 👋
              </Title>
              <Paragraph className="welcome-subtitle">
                欢迎使用 OpenCode Web 平台，开始您的高效工作之旅
              </Paragraph>
            </div>
          </Col>
          <Col>
            <div className="welcome-date">
              <DashboardOutlined />
              <Text>
                {new Date().toLocaleDateString('zh-CN', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  weekday: 'long',
                })}
              </Text>
            </div>
          </Col>
        </Row>
      </Card>

      {/* 快速操作 */}
      <QuickActions />

      {/* 统计卡片 */}
      <div className="stats-section">
        {loading ? (
          <Row gutter={[16, 16]}>
            {[1, 2, 3, 4].map((i) => (
              <Col xs={12} sm={6} key={i}>
                <Card bordered={false}>
                  <Skeleton active paragraph={false} />
                </Card>
              </Col>
            ))}
          </Row>
        ) : (
          <StatsCards />
        )}
      </div>

      {/* 最近使用 */}
      <Row gutter={[16, 16]} className="recent-section">
        <Col xs={24} lg={8}>
          <RecentList
            title="最近会话"
            icon={<MessageOutlined />}
            items={recentSessions}
            type="session"
            emptyText="暂无会话记录"
            viewAllPath="/chat"
          />
        </Col>
        <Col xs={24} lg={8}>
          <RecentList
            title="最近技能"
            icon={<AppstoreOutlined />}
            items={recentSkills}
            type="skill"
            emptyText="暂无使用记录"
            viewAllPath="/skills"
          />
        </Col>
        <Col xs={24} lg={8}>
          <RecentList
            title="最近工作流"
            icon={<PartitionOutlined />}
            items={recentWorkflows}
            type="workflow"
            emptyText="暂无运行记录"
            viewAllPath="/workflows"
          />
        </Col>
      </Row>

      {/* 快速入口 */}
      <Card className="quick-entry-card" bordered={false}>
        <div className="quick-entry-title">
          <RocketOutlined /> 快速开始
        </div>
        <Row gutter={[16, 16]}>
          <Col xs={12} sm={6}>
            <div
              className="quick-entry-item"
              onClick={() => navigate('/skills')}
            >
              <div className="entry-icon skills">
                <AppstoreOutlined />
              </div>
              <Text>浏览技能市场</Text>
            </div>
          </Col>
          <Col xs={12} sm={6}>
            <div
              className="quick-entry-item"
              onClick={() => navigate('/workflows')}
            >
              <div className="entry-icon workflows">
                <PartitionOutlined />
              </div>
              <Text>管理工作流</Text>
            </div>
          </Col>
          <Col xs={12} sm={6}>
            <div
              className="quick-entry-item"
              onClick={() => navigate('/monitoring')}
            >
              <div className="entry-icon monitoring">
                <DashboardOutlined />
              </div>
              <Text>查看监控</Text>
            </div>
          </Col>
          <Col xs={12} sm={6}>
            <div
              className="quick-entry-item"
              onClick={() => navigate('/settings')}
            >
              <div className="entry-icon settings">
                <ThunderboltOutlined />
              </div>
              <Text>系统设置</Text>
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  )
}
