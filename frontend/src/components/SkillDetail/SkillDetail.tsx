import React, { useState } from 'react'
import {
  Drawer,
  Descriptions,
  Tag,
  Button,
  Tabs,
  Typography,
  Space,
  Divider,
  Avatar,
  message,
} from 'antd'
import {
  DownloadOutlined,
  StarFilled,
  LinkOutlined,
  GithubOutlined,
  BookOutlined,
  UserOutlined,
  CalendarOutlined,
  HistoryOutlined,
  AppstoreAddOutlined,
} from '@ant-design/icons'
import type { PublishedSkill } from '@/api/skillSearch'
import RatingDisplay from '@/components/RatingDisplay'
import CommentSection from '@/components/CommentSection'
import FavoriteButton from '@/components/FavoriteButton'
import './SkillDetail.css'

const { Title, Paragraph, Text } = Typography

interface SkillDetailProps {
  skill: PublishedSkill | null
  open: boolean
  onClose: () => void
  onInstall?: (skillId: number) => void
  installLoading?: boolean
  currentUserId?: number
}

export default function SkillDetail({
  skill,
  open,
  onClose,
  onInstall,
  installLoading,
  currentUserId,
}: SkillDetailProps) {
  const [activeTab, setActiveTab] = useState('description')

  if (!skill) return null

  const isPaid = parseFloat(skill.price) > 0

  const handleInstall = () => {
    onInstall?.(skill.id)
  }

  const handleRatingChange = (rating: number) => {
    message.success(`评分成功: ${rating} 星`)
  }

  return (
    <Drawer
      title={null}
      placement="right"
      onClose={onClose}
      open={open}
      width={700}
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
        <Space style={{ width: '100%' }} direction="vertical">
          <Button
            type="primary"
            size="large"
            icon={<DownloadOutlined />}
            onClick={handleInstall}
            loading={installLoading}
            block
          >
            {isPaid ? `¥${skill.price} - 购买并安装` : '安装'}
          </Button>
          <FavoriteButton skillId={skill.id} size="large" block />
        </Space>
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
      <Tabs activeKey={activeTab} onChange={setActiveTab} className="detail-tabs">
        <Tabs.TabPane tab="简介" key="description">
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

            {/* 使用说明 */}
            <Title level={5} style={{ marginTop: 24 }}>
              <BookOutlined style={{ marginRight: 8 }} />
              使用说明
            </Title>
            <Paragraph type="secondary">
              {skill.documentation_url ? (
                <a href={skill.documentation_url} target="_blank" rel="noopener noreferrer">
                  查看完整使用文档 <LinkOutlined />
                </a>
              ) : (
                '安装后可在技能列表中查看使用说明'
              )}
            </Paragraph>
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane tab="详情" key="details">
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

            {/* 版本历史提示 */}
            <Divider />
            <Title level={5}>
              <HistoryOutlined style={{ marginRight: 8 }} />
              版本历史
            </Title>
            <Text type="secondary">
              当前版本: v{skill.version}
            </Text>
            <Paragraph type="secondary" style={{ marginTop: 8 }}>
              完整版本历史请在代码仓库中查看
            </Paragraph>
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane tab="评分与评论" key="reviews">
          <div className="tab-content">
            {/* 评分展示 */}
            <RatingDisplay
              skillId={skill.id}
              showUserRating={true}
              onRatingChange={handleRatingChange}
            />

            <Divider />

            {/* 评论区 */}
            <CommentSection skillId={skill.id} currentUserId={currentUserId} />
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane tab="相关推荐" key="related">
          <div className="tab-content">
            <Title level={5}>
              <AppstoreAddOutlined style={{ marginRight: 8 }} />
              相关技能
            </Title>
            <Text type="secondary">
              基于分类和标签的相关推荐功能即将上线...
            </Text>
            <div className="related-placeholder">
              <Paragraph type="secondary">
                即将推出基于 AI 的智能推荐功能，为您推荐相似技能
              </Paragraph>
            </div>
          </div>
        </Tabs.TabPane>
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
