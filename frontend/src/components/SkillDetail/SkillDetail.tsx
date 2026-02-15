import React from 'react'
import {
  Drawer,
  Descriptions,
  Tag,
  Button,
  Rate,
  Tabs,
  Typography,
  Space,
  Divider,
  Avatar,
  Tooltip,
} from 'antd'
import {
  DownloadOutlined,
  StarFilled,
  LinkOutlined,
  GithubOutlined,
  BookOutlined,
  UserOutlined,
  CalendarOutlined,
} from '@ant-design/icons'
import type { PublishedSkill } from '@/api/skillSearch'
import './SkillDetail.css'

const { Title, Paragraph, Text } = Typography
const { TabPane } = Tabs

interface SkillDetailProps {
  skill: PublishedSkill | null
  open: boolean
  onClose: () => void
  onInstall?: (skillId: number) => void
  installLoading?: boolean
}

export default function SkillDetail({
  skill,
  open,
  onClose,
  onInstall,
  installLoading,
}: SkillDetailProps) {
  if (!skill) return null
  
  const isPaid = parseFloat(skill.price) > 0
  
  return (
    <Drawer
      title={null}
      placement="right"
      onClose={onClose}
      open={open}
      width={600}
      className="skill-detail-drawer"
    >
      {/* 头部 */}
      <div className="detail-header">
        <div className="detail-icon">
          {skill.name.charAt(0).toUpperCase()}
        </div>
        <div className="detail-title-section">
          <Title level={3} className="detail-title">
            {skill.name}
            {skill.is_featured && <Tag color="gold" style={{ marginLeft: 8 }}>精选</Tag>}
          </Title>
          <Space wrap>
            <Tag color="blue">{skill.category || '通用'}</Tag>
            <Tag>v{skill.version}</Tag>
            {isPaid && <Tag color="green">¥{skill.price}</Tag>}
            {!isPaid && <Tag color="green">免费</Tag>}
          </Space>
        </div>
      </div>
      
      {/* 操作按钮 */}
      <div className="detail-actions">
        <Button
          type="primary"
          size="large"
          icon={<DownloadOutlined />}
          onClick={() => onInstall?.(skill.id)}
          loading={installLoading}
          block
        >
          {isPaid ? `¥${skill.price} - 购买并安装` : '安装'}
        </Button>
      </div>
      
      {/* 统计信息 */}
      <div className="detail-stats">
        <div className="stat-box">
          <div className="stat-value">
            <StarFilled className="star-icon" />
            {parseFloat(skill.rating).toFixed(1)}
          </div>
          <div className="stat-label">评分</div>
        </div>
        <div className="stat-box">
          <div className="stat-value">{skill.rating_count}</div>
          <div className="stat-label">评价</div>
        </div>
        <div className="stat-box">
          <div className="stat-value">{skill.download_count.toLocaleString()}</div>
          <div className="stat-label">下载</div>
        </div>
        <div className="stat-box">
          <div className="stat-value">{skill.install_count.toLocaleString()}</div>
          <div className="stat-label">安装</div>
        </div>
      </div>
      
      <Divider />
      
      {/* 标签页 */}
      <Tabs defaultActiveKey="description" className="detail-tabs">
        <TabPane tab="简介" key="description">
          <div className="tab-content">
            <Title level={5}>描述</Title>
            <Paragraph className="description-text">
              {skill.description || '暂无描述'}
            </Paragraph>
            
            {skill.tags && skill.tags.length > 0 && (
              <>
                <Title level={5} style={{ marginTop: 24 }}>标签</Title>
                <Space wrap>
                  {skill.tags.map((tag) => (
                    <Tag key={tag}>{tag}</Tag>
                  ))}
                </Space>
              </>
            )}
          </div>
        </TabPane>
        
        <TabPane tab="详情" key="details">
          <div className="tab-content">
            <Descriptions column={1} labelStyle={{ fontWeight: 500 }}>
              <Descriptions.Item label="版本">{skill.version}</Descriptions.Item>
              <Descriptions.Item label="分类">{skill.category || '通用'}</Descriptions.Item>
              <Descriptions.Item label="许可证">{skill.license}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={skill.status === 'published' ? 'success' : 'default'}>
                  {skill.status === 'published' ? '已发布' : skill.status}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                <CalendarOutlined style={{ marginRight: 8 }} />
                {new Date(skill.created_at).toLocaleDateString('zh-CN')}
              </Descriptions.Item>
              <Descriptions.Item label="发布时间">
                <CalendarOutlined style={{ marginRight: 8 }} />
                {skill.published_at 
                  ? new Date(skill.published_at).toLocaleDateString('zh-CN')
                  : '未发布'
                }
              </Descriptions.Item>
            </Descriptions>
            
            {/* 链接 */}
            <Divider />
            <Title level={5}>链接</Title>
            <Space direction="vertical" style={{ width: '100%' }}>
              {skill.homepage_url && (
                <a href={skill.homepage_url} target="_blank" rel="noopener noreferrer">
                  <Button icon={<LinkOutlined />} block>主页</Button>
                </a>
              )}
              {skill.repository_url && (
                <a href={skill.repository_url} target="_blank" rel="noopener noreferrer">
                  <Button icon={<GithubOutlined />} block>代码仓库</Button>
                </a>
              )}
              {skill.documentation_url && (
                <a href={skill.documentation_url} target="_blank" rel="noopener noreferrer">
                  <Button icon={<BookOutlined />} block>文档</Button>
                </a>
              )}
            </Space>
          </div>
        </TabPane>
        
        <TabPane tab="评分与评论" key="reviews">
          <div className="tab-content">
            <div className="rating-summary">
              <div className="rating-big">
                <div className="rating-number">{parseFloat(skill.rating).toFixed(1)}</div>
                <Rate disabled value={parseFloat(skill.rating)} allowHalf />
                <div className="rating-count">{skill.rating_count} 个评价</div>
              </div>
            </div>
            <Divider />
            <div className="reviews-placeholder">
              <Text type="secondary">
                评论功能即将上线...
              </Text>
            </div>
          </div>
        </TabPane>
      </Tabs>
      
      {/* 底部信息 */}
      <div className="detail-footer">
        <Avatar icon={<UserOutlined />} size="small" />
        <Text type="secondary" style={{ marginLeft: 8 }}>
          发布者 ID: {skill.publisher_id}
        </Text>
      </div>
    </Drawer>
  )
}
