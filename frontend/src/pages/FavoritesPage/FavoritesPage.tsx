import React from 'react'
import { List, Card, Empty, Spin, Pagination, Button, Rate, Tag, message } from 'antd'
import { StarFilled, DeleteOutlined, DownloadOutlined, CalendarOutlined } from '@ant-design/icons'
import { useFavorites, useRemoveFavorite } from '@/hooks/useFavorites'
import type { Favorite } from '@/types/comments'
import './FavoritesPage.css'

const { Text, Title } = Typography
import { Typography } from 'antd'

export default function FavoritesPage() {
  const [page, setPage] = React.useState(1)
  const pageSize = 12

  const { data, isLoading, refetch } = useFavorites(page, pageSize)
  const removeFavorite = useRemoveFavorite()

  const handleRemove = async (skillId: number, skillName: string) => {
    try {
      await removeFavorite.mutateAsync(skillId)
      message.success(`已取消收藏 ${skillName}`)
      refetch()
    } catch (error) {
      message.error('操作失败，请重试')
    }
  }

  const renderFavoriteItem = (favorite: Favorite) => {
    const skill = favorite.skill
    
    if (!skill) return null

    return (
      <Card
        hoverable
        className="favorite-card"
        actions={[
          <Button 
            type="text" 
            icon={<DownloadOutlined />}
            onClick={() => {
              // TODO: 跳转到技能详情或安装
              message.info('即将开放')
            }}
          >
            安装
          </Button>,
          <Button 
            type="text" 
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleRemove(skill.id, skill.name)}
            loading={removeFavorite.isPending}
          >
            移除
          </Button>,
        ]}
      >
        <Card.Meta
          avatar={
            <div className="skill-icon">
              {skill.name.charAt(0).toUpperCase()}
            </div>
          }
          title={
            <div className="card-title">
              <span className="skill-name">{skill.name}</span>
              <Tag>v{skill.version}</Tag>
            </div>
          }
          description={
            <div className="card-description">
              <Text ellipsis={{ rows: 2 }}>
                {skill.description || '暂无描述'}
              </Text>
            </div>
          }
        />
        
        <div className="card-stats">
          <div className="stat-item">
            <StarFilled className="star-icon" />
            <Text>{parseFloat(skill.rating).toFixed(1)}</Text>
          </div>
          <div className="stat-item">
            <DownloadOutlined />
            <Text>{skill.download_count}</Text>
          </div>
          <div className="stat-item">
            <CalendarOutlined />
            <Text>{new Date(favorite.created_at).toLocaleDateString('zh-CN')}</Text>
          </div>
        </div>
      </Card>
    )
  }

  return (
    <div className="favorites-page">
      <div className="page-header">
        <Title level={2}>
          <StarFilled className="header-icon" />
          我的收藏
        </Title>
        <Text type="secondary">
          共 {data?.total || 0} 个收藏
        </Text>
      </div>

      <Spin spinning={isLoading}>
        {data?.items && data.items.length > 0 ? (
          <>
            <List
              grid={{
                gutter: 16,
                xs: 1,
                sm: 2,
                md: 3,
                lg: 3,
                xl: 4,
                xxl: 4,
              }}
              dataSource={data.items}
              renderItem={renderFavoriteItem}
              className="favorites-list"
            />
            
            {data.has_more && (
              <div className="pagination-wrapper">
                <Pagination
                  current={page}
                  pageSize={pageSize}
                  total={data.total}
                  onChange={(p) => setPage(p)}
                  showSizeChanger={false}
                  showTotal={(total) => `共 ${total} 个收藏`}
                />
              </div>
            )}
          </>
        ) : (
          <Empty
            description="暂无收藏"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" href="/skills-hub">
              去浏览技能
            </Button>
          </Empty>
        )}
      </Spin>
    </div>
  )
}
