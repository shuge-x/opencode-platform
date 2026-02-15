import React from 'react'
import { Spin, Skeleton, Card, Space, Typography } from 'antd'
import { LoadingOutlined } from '@ant-design/icons'

const { Text } = Typography

interface LoadingSpinnerProps {
  size?: 'small' | 'default' | 'large'
  tip?: string
  fullScreen?: boolean
}

/**
 * Loading Spinner Component
 */
export function LoadingSpinner({ 
  size = 'default', 
  tip = '加载中...', 
  fullScreen = false 
}: LoadingSpinnerProps) {
  const spinner = (
    <Spin
      indicator={<LoadingOutlined style={{ fontSize: size === 'large' ? 48 : size === 'small' ? 16 : 24 }} spin />}
      tip={tip}
      size={size}
    />
  )

  if (fullScreen) {
    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(255, 255, 255, 0.8)',
        zIndex: 9999
      }}>
        {spinner}
      </div>
    )
  }

  return spinner
}

interface LoadingCardProps {
  rows?: number
  avatar?: boolean
  title?: boolean
}

/**
 * Loading Card Skeleton
 */
export function LoadingCard({ rows = 3, avatar = true, title = true }: LoadingCardProps) {
  return (
    <Card>
      <Skeleton
        avatar={avatar}
        paragraph={{ rows }}
        active
        title={title}
      />
    </Card>
  )
}

interface LoadingListProps {
  count?: number
}

/**
 * Loading List Skeleton
 */
export function LoadingList({ count = 5 }: LoadingListProps) {
  return (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      {Array.from({ length: count }).map((_, index) => (
        <Card key={index} size="small">
          <Skeleton
            avatar
            paragraph={{ rows: 1 }}
            active
            title={{ width: '60%' }}
          />
        </Card>
      ))}
    </Space>
  )
}

interface LoadingTableProps {
  rows?: number
  columns?: number
}

/**
 * Loading Table Skeleton
 */
export function LoadingTable({ rows = 5, columns = 4 }: LoadingTableProps) {
  return (
    <div style={{ padding: '16px 0' }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        gap: 16, 
        padding: '12px 16px', 
        background: '#fafafa',
        borderBottom: '1px solid #f0f0f0'
      }}>
        {Array.from({ length: columns }).map((_, i) => (
          <div key={i} style={{ flex: 1 }}>
            <div style={{ 
              height: 16, 
              background: '#e8e8e8', 
              borderRadius: 4,
              width: `${60 + Math.random() * 40}%`
            }} />
          </div>
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div 
          key={rowIndex} 
          style={{ 
            display: 'flex', 
            gap: 16, 
            padding: '16px',
            borderBottom: '1px solid #f0f0f0'
          }}
        >
          {Array.from({ length: columns }).map((_, colIndex) => (
            <div key={colIndex} style={{ flex: 1 }}>
              <div style={{ 
                height: 14, 
                background: '#f0f0f0', 
                borderRadius: 4,
                width: `${40 + Math.random() * 50}%`
              }} />
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

interface LoadingOverlayProps {
  visible: boolean
  tip?: string
}

/**
 * Loading Overlay for containers
 */
export function LoadingOverlay({ visible, tip = '处理中...' }: LoadingOverlayProps) {
  if (!visible) return null

  return (
    <div style={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'rgba(255, 255, 255, 0.7)',
      zIndex: 10,
      borderRadius: 'inherit'
    }}>
      <div style={{ textAlign: 'center' }}>
        <Spin size="large" />
        {tip && <Text style={{ display: 'block', marginTop: 12 }}>{tip}</Text>}
      </div>
    </div>
  )
}

interface PageLoadingProps {
  tip?: string
}

/**
 * Full Page Loading
 */
export function PageLoading({ tip = '页面加载中...' }: PageLoadingProps) {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexDirection: 'column',
      gap: 16
    }}>
      <Spin size="large" />
      <Text type="secondary">{tip}</Text>
    </div>
  )
}

/**
 * Delayed Loading - Shows loading only after a delay to avoid flash
 */
export function DelayedLoading({ 
  children, 
  loading, 
  delay = 300 
}: { 
  children: React.ReactNode
  loading: boolean
  delay?: number 
}) {
  const [showLoading, setShowLoading] = React.useState(false)

  React.useEffect(() => {
    if (loading) {
      const timer = setTimeout(() => setShowLoading(true), delay)
      return () => clearTimeout(timer)
    } else {
      setShowLoading(false)
    }
  }, [loading, delay])

  if (!loading) {
    return <>{children}</>
  }

  if (!showLoading) {
    return <>{children}</>
  }

  return <LoadingSpinner />
}

export default LoadingSpinner
