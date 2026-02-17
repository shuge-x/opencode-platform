import React from 'react'
import { Skeleton as AntSkeleton, Card, Space, Row, Col } from 'antd'

/**
 * 列表骨架屏
 */
interface ListSkeletonProps {
  count?: number
  avatar?: boolean
  rows?: number
}

export function ListSkeleton({ count = 5, avatar = true, rows = 1 }: ListSkeletonProps) {
  return (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      {Array.from({ length: count }).map((_, index) => (
        <Card key={index} size="small" style={{ marginBottom: 8 }}>
          <AntSkeleton
            avatar={avatar}
            paragraph={{ rows }}
            active
            title={{ width: '60%' }}
          />
        </Card>
      ))}
    </Space>
  )
}

/**
 * 详情骨架屏
 */
interface DetailSkeletonProps {
  rows?: number
  avatar?: boolean
  hasImage?: boolean
}

export function DetailSkeleton({ rows = 4, avatar = true, hasImage = false }: DetailSkeletonProps) {
  return (
    <div>
      {/* 标题区域 */}
      <AntSkeleton
        avatar={avatar}
        paragraph={{ rows: 2 }}
        active
        title={{ width: '40%' }}
        style={{ marginBottom: 24 }}
      />
      
      {/* 图片占位 */}
      {hasImage && (
        <div style={{ 
          height: 200, 
          background: '#f5f5f5', 
          borderRadius: 8, 
          marginBottom: 24,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#bfbfbf'
        }}>
          <AntSkeleton.Image style={{ width: '100%', height: 200 }} active />
        </div>
      )}
      
      {/* 内容区域 */}
      <Card style={{ marginBottom: 16 }}>
        <AntSkeleton paragraph={{ rows }} active title={false} />
      </Card>
      
      {/* 标签/属性区域 */}
      <Row gutter={16}>
        {Array.from({ length: 3 }).map((_, i) => (
          <Col span={8} key={i}>
            <Card size="small">
              <AntSkeleton paragraph={{ rows: 1 }} active title={{ width: '50%' }} />
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  )
}

/**
 * 卡片骨架屏
 */
interface CardSkeletonProps {
  count?: number
  showImage?: boolean
  rows?: number
}

export function CardSkeleton({ count = 4, showImage = true, rows = 2 }: CardSkeletonProps) {
  return (
    <Row gutter={[16, 16]}>
      {Array.from({ length: count }).map((_, index) => (
        <Col xs={24} sm={12} md={8} lg={6} key={index}>
          <Card>
            {showImage && (
              <AntSkeleton.Image 
                style={{ width: '100%', height: 120, marginBottom: 16 }} 
                active 
              />
            )}
            <AntSkeleton
              paragraph={{ rows }}
              active
              title={{ width: '70%' }}
            />
          </Card>
        </Col>
      ))}
    </Row>
  )
}

/**
 * 表格骨架屏
 */
interface TableSkeletonProps {
  rows?: number
  columns?: number
}

export function TableSkeleton({ rows = 5, columns = 4 }: TableSkeletonProps) {
  return (
    <div style={{ padding: '16px 0' }}>
      {/* 表头 */}
      <div style={{
        display: 'flex',
        gap: 16,
        padding: '12px 16px',
        background: '#fafafa',
        borderBottom: '1px solid #f0f0f0',
        borderTopLeftRadius: 8,
        borderTopRightRadius: 8
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
      {/* 表格行 */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div
          key={rowIndex}
          style={{
            display: 'flex',
            gap: 16,
            padding: '16px',
            borderBottom: '1px solid #f0f0f0',
            background: rowIndex % 2 === 0 ? '#fff' : '#fafafa'
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

/**
 * 表单骨架屏
 */
interface FormSkeletonProps {
  fields?: number
}

export function FormSkeleton({ fields = 4 }: FormSkeletonProps) {
  return (
    <div>
      {Array.from({ length: fields }).map((_, index) => (
        <div key={index} style={{ marginBottom: 24 }}>
          {/* 标签 */}
          <div style={{
            height: 14,
            width: `${30 + Math.random() * 20}%`,
            background: '#e8e8e8',
            borderRadius: 4,
            marginBottom: 8
          }} />
          {/* 输入框占位 */}
          <div style={{
            height: 32,
            width: '100%',
            background: '#f5f5f5',
            borderRadius: 6
          }} />
        </div>
      ))}
      {/* 按钮 */}
      <div style={{ marginTop: 24 }}>
        <div style={{
          height: 32,
          width: 100,
          background: '#1890ff',
          borderRadius: 6
        }} />
      </div>
    </div>
  )
}

/**
 * 评论骨架屏
 */
interface CommentSkeletonProps {
  count?: number
}

export function CommentSkeleton({ count = 3 }: CommentSkeletonProps) {
  return (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} style={{ display: 'flex', gap: 12 }}>
          {/* 头像 */}
          <div style={{
            width: 40,
            height: 40,
            borderRadius: '50%',
            background: '#f0f0f0',
            flexShrink: 0
          }} />
          <div style={{ flex: 1 }}>
            {/* 用户名和时间 */}
            <div style={{ display: 'flex', gap: 12, marginBottom: 8 }}>
              <div style={{ height: 14, width: 80, background: '#e8e8e8', borderRadius: 4 }} />
              <div style={{ height: 14, width: 60, background: '#f0f0f0', borderRadius: 4 }} />
            </div>
            {/* 评论内容 */}
            <div style={{ height: 40, background: '#f5f5f5', borderRadius: 4, width: '100%' }} />
          </div>
        </div>
      ))}
    </Space>
  )
}

/**
 * 统计卡片骨架屏
 */
interface StatCardSkeletonProps {
  count?: number
}

export function StatCardSkeleton({ count = 4 }: StatCardSkeletonProps) {
  return (
    <Row gutter={16}>
      {Array.from({ length: count }).map((_, index) => (
        <Col xs={12} sm={6} key={index}>
          <Card size="small">
            <div style={{ marginBottom: 8 }}>
              <div style={{
                height: 12,
                width: '40%',
                background: '#e8e8e8',
                borderRadius: 4
              }} />
            </div>
            <div style={{
              height: 28,
              width: '60%',
              background: '#f0f0f0',
              borderRadius: 4
            }} />
          </Card>
        </Col>
      ))}
    </Row>
  )
}

export default {
  ListSkeleton,
  DetailSkeleton,
  CardSkeleton,
  TableSkeleton,
  FormSkeleton,
  CommentSkeleton,
  StatCardSkeleton
}
