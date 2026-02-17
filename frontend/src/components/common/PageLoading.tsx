import { useEffect, useState } from 'react'
import { Skeleton, Card, Space, Typography } from 'antd'
import {
  MessageOutlined,
  AppstoreOutlined,
  PartitionOutlined,
} from '@ant-design/icons'
import './PageLoading.css'

const { Text } = Typography

/* ========== 顶部进度条 ========== */

interface TopProgressBarProps {
  loading: boolean
  color?: string
  height?: number
}

/**
 * 顶部进度条组件 (NProgress 风格)
 */
export function TopProgressBar({
  loading,
  color = '#1890ff',
  height = 3,
}: TopProgressBarProps) {
  const [progress, setProgress] = useState(0)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (loading) {
      setVisible(true)
      setProgress(0)

      // 模拟进度
      const timer1 = setTimeout(() => setProgress(30), 100)
      const timer2 = setTimeout(() => setProgress(60), 300)
      const timer3 = setTimeout(() => setProgress(80), 600)

      return () => {
        clearTimeout(timer1)
        clearTimeout(timer2)
        clearTimeout(timer3)
      }
    } else {
      setProgress(100)
      const timer = setTimeout(() => {
        setVisible(false)
        setProgress(0)
      }, 300)
      return () => clearTimeout(timer)
    }
  }, [loading])

  if (!visible) return null

  return (
    <div
      className="top-progress-bar"
      style={{ height }}
    >
      <div
        className="top-progress-inner"
        style={{
          width: `${progress}%`,
          background: color,
          transition: progress === 100 ? 'width 0.2s ease' : 'width 0.4s ease',
        }}
      />
    </div>
  )
}

/* ========== 页面骨架屏 ========== */

/**
 * 首页骨架屏
 */
export function HomeSkeleton() {
  return (
    <div className="page-skeleton home-skeleton">
      {/* 欢迎卡片骨架 */}
      <Card className="skeleton-card welcome-skeleton" bordered={false}>
        <Skeleton active paragraph={{ rows: 1 }} />
      </Card>

      {/* 快速操作骨架 */}
      <Card className="skeleton-card" bordered={false}>
        <div className="skeleton-actions">
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton-action-item">
              <Skeleton.Button active style={{ width: '100%', height: 56 }} />
            </div>
          ))}
        </div>
      </Card>

      {/* 统计卡片骨架 */}
      <div className="skeleton-stats">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="skeleton-card stats-skeleton" bordered={false}>
            <Skeleton active paragraph={false} />
          </Card>
        ))}
      </div>

      {/* 最近列表骨架 */}
      <div className="skeleton-recent">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="skeleton-card" bordered={false}>
            <Skeleton active paragraph={{ rows: 3 }} />
          </Card>
        ))}
      </div>
    </div>
  )
}

/**
 * 列表页骨架屏
 */
export function ListSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="page-skeleton list-skeleton">
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i} className="skeleton-card list-item-skeleton" bordered={false}>
          <Skeleton avatar active paragraph={{ rows: 2 }} />
        </Card>
      ))}
    </div>
  )
}

/**
 * 卡片网格骨架屏
 */
export function CardGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="page-skeleton card-grid-skeleton">
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i} className="skeleton-card card-skeleton" bordered={false}>
          <Skeleton active avatar={false} paragraph={{ rows: 3 }} />
        </Card>
      ))}
    </div>
  )
}

/**
 * 详情页骨架屏
 */
export function DetailSkeleton() {
  return (
    <div className="page-skeleton detail-skeleton">
      <Card className="skeleton-card" bordered={false}>
        <Skeleton active paragraph={{ rows: 4 }} />
      </Card>
      <Card className="skeleton-card" bordered={false}>
        <Skeleton active paragraph={{ rows: 6 }} />
      </Card>
    </div>
  )
}

/* ========== 空状态组件 ========== */

interface EmptyStateProps {
  type: 'session' | 'skill' | 'workflow' | 'generic'
  title?: string
  description?: string
  actionText?: string
  onAction?: () => void
}

/**
 * 空状态组件
 */
export function EmptyState({
  type,
  title,
  description,
  actionText,
  onAction,
}: EmptyStateProps) {
  const config = {
    session: {
      icon: <MessageOutlined className="empty-icon session" />,
      defaultTitle: '暂无会话',
      defaultDescription: '开始一个新的对话，探索 AI 的强大功能',
      defaultAction: '新建会话',
    },
    skill: {
      icon: <AppstoreOutlined className="empty-icon skill" />,
      defaultTitle: '暂无技能',
      defaultDescription: '浏览技能市场，发现更多实用工具',
      defaultAction: '浏览技能',
    },
    workflow: {
      icon: <PartitionOutlined className="empty-icon workflow" />,
      defaultTitle: '暂无工作流',
      defaultDescription: '创建您的第一个工作流，实现任务自动化',
      defaultAction: '创建工作流',
    },
    generic: {
      icon: <AppstoreOutlined className="empty-icon generic" />,
      defaultTitle: '暂无数据',
      defaultDescription: '这里空空如也',
      defaultAction: '刷新',
    },
  }

  const { icon, defaultTitle, defaultDescription, defaultAction } = config[type]

  return (
    <div className="empty-state-container">
      <div className="empty-state-content">
        <div className="empty-icon-wrapper">{icon}</div>
        <Text className="empty-title">{title || defaultTitle}</Text>
        <Text className="empty-description">{description || defaultDescription}</Text>
        {actionText && onAction && (
          <button className="empty-action-btn" onClick={onAction}>
            {actionText || defaultAction}
          </button>
        )}
      </div>
    </div>
  )
}

/* ========== 加载包装器 ========== */

interface PageLoadingWrapperProps {
  loading: boolean
  skeleton?: React.ReactNode
  children: React.ReactNode
  showProgressBar?: boolean
}

/**
 * 页面加载包装器
 */
export function PageLoadingWrapper({
  loading,
  skeleton,
  children,
  showProgressBar = true,
}: PageLoadingWrapperProps) {
  return (
    <>
      {showProgressBar && <TopProgressBar loading={loading} />}
      {loading ? (skeleton || <HomeSkeleton />) : children}
    </>
  )
}

export default PageLoadingWrapper
