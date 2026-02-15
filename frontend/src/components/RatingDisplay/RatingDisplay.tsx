import React from 'react'
import { Rate, Progress, Typography, Space, Statistic } from 'antd'
import { StarFilled, UserOutlined } from '@ant-design/icons'
import type { SkillRating, RatingDistribution } from '@/types/comments'
import { useSkillRating, useUserRating, useCreateOrUpdateRating } from '@/hooks/useRatings'
import './RatingDisplay.css'

const { Text, Title } = Typography

interface RatingDisplayProps {
  skillId: number
  showUserRating?: boolean
  onRatingChange?: (rating: number) => void
}

export default function RatingDisplay({ 
  skillId, 
  showUserRating = true,
  onRatingChange 
}: RatingDisplayProps) {
  const { data: ratingData, isLoading } = useSkillRating(skillId)
  const { data: userRating } = useUserRating(skillId)
  const createRating = useCreateOrUpdateRating()

  const handleRatingChange = (value: number) => {
    createRating.mutate(
      { skill_id: skillId, rating: value },
      {
        onSuccess: () => {
          onRatingChange?.(value)
        }
      }
    )
  }

  if (isLoading) {
    return <div className="rating-loading">加载中...</div>
  }

  const distribution = ratingData?.rating_distribution || {
    five_star: 0,
    four_star: 0,
    three_star: 0,
    two_star: 0,
    one_star: 0,
  }

  const total = ratingData?.rating_count || 0
  const avgRating = ratingData?.average_rating || 0

  // 计算各星级百分比
  const getPercentage = (count: number) => {
    if (total === 0) return 0
    return Math.round((count / total) * 100)
  }

  return (
    <div className="rating-display">
      {/* 总体评分 */}
      <div className="rating-summary">
        <div className="rating-score">
          <div className="score-number">{avgRating.toFixed(1)}</div>
          <Rate disabled allowHalf value={avgRating} className="summary-rate" />
          <div className="total-ratings">
            <UserOutlined /> {total} 个评价
          </div>
        </div>

        {/* 评分分布 */}
        <div className="rating-distribution">
          {[5, 4, 3, 2, 1].map((star) => {
            const key = `${star}_star` as keyof RatingDistribution
            const count = distribution[key] || 0
            return (
              <div key={star} className="distribution-row">
                <Text className="star-label">{star} 星</Text>
                <Progress
                  percent={getPercentage(count)}
                  showInfo={false}
                  strokeColor="#fadb14"
                  trailColor="#f0f0f0"
                  className="distribution-bar"
                />
                <Text className="count-label">{count}</Text>
              </div>
            )
          })}
        </div>
      </div>

      {/* 用户评分 */}
      {showUserRating && (
        <div className="user-rating">
          <Title level={5}>我的评分</Title>
          <Space>
            <Rate
              value={userRating?.rating || 0}
              onChange={handleRatingChange}
              allowClear
              disabled={createRating.isPending}
            />
            {userRating && (
              <Text type="secondary">
                已评分于 {new Date(userRating.created_at).toLocaleDateString('zh-CN')}
              </Text>
            )}
          </Space>
        </div>
      )}
    </div>
  )
}
