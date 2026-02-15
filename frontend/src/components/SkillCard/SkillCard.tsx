import React from 'react'
import { Card, Tag, Button, Rate, Dropdown } from 'antd'
import {
  StarFilled,
  DownloadOutlined,
  MoreOutlined,
  ShareAltOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'
import type { PublishedSkill } from '@/api/skillSearch'
import './SkillCard.css'

interface SkillCardProps {
  skill: PublishedSkill
  onInstall?: (skillId: number) => void
  onViewDetail?: (skill: PublishedSkill) => void
  loading?: boolean
}

export default function SkillCard({ skill, onInstall, onViewDetail, loading }: SkillCardProps) {
  const isPaid = parseFloat(skill.price) > 0
  
  const menuItems = [
    {
      key: 'detail',
      icon: <InfoCircleOutlined />,
      label: '查看详情',
      onClick: () => onViewDetail?.(skill),
    },
    {
      key: 'share',
      icon: <ShareAltOutlined />,
      label: '分享',
      onClick: () => {
        navigator.clipboard?.writeText(window.location.href)
      },
    },
  ]
  
  return (
    <Card
      hoverable
      className="skill-card"
      cover={
        <div className="skill-card-cover">
          <div className="skill-icon">
            {skill.name.charAt(0).toUpperCase()}
          </div>
          {skill.is_featured && (
            <Tag color="gold" className="featured-tag">精选</Tag>
          )}
          <Dropdown menu={{ items: menuItems }} trigger={['click']}>
            <Button
              type="text"
              className="more-btn"
              icon={<MoreOutlined />}
              onClick={(e) => e.stopPropagation()}
            />
          </Dropdown>
        </div>
      }
      actions={[
        <Button
          type="primary"
          block
          onClick={() => onInstall?.(skill.id)}
          loading={loading}
        >
          {isPaid ? `¥${skill.price}` : '安装'}
        </Button>,
      ]}
    >
      <Card.Meta
        title={
          <div className="skill-title">
            <span className="skill-name">{skill.name}</span>
            {skill.category && (
              <Tag color="blue" className="category-tag">{skill.category}</Tag>
            )}
          </div>
        }
        description={
          <div className="skill-description">
            {skill.description || '暂无描述'}
          </div>
        }
      />
      <div className="skill-stats">
        <div className="stat-item">
          <Rate disabled value={parseFloat(skill.rating)} allowHalf className="mini-rate" />
          <span className="rating-text">{parseFloat(skill.rating).toFixed(1)}</span>
          <span className="stat-secondary">({skill.rating_count})</span>
        </div>
        <div className="stat-item">
          <DownloadOutlined />
          <span>{skill.download_count.toLocaleString()}</span>
        </div>
        <Tag className="version-tag">v{skill.version}</Tag>
      </div>
      {skill.tags && skill.tags.length > 0 && (
        <div className="skill-tags">
          {skill.tags.slice(0, 3).map((tag) => (
            <Tag key={tag} className="skill-tag">{tag}</Tag>
          ))}
          {skill.tags.length > 3 && <span className="more-tags">+{skill.tags.length - 3}</span>}
        </div>
      )}
    </Card>
  )
}
