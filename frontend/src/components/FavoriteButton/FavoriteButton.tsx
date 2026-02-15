import React from 'react'
import { Button, Tooltip, message } from 'antd'
import { StarOutlined, StarFilled } from '@ant-design/icons'
import { useToggleFavorite } from '@/hooks/useFavorites'
import './FavoriteButton.css'

interface FavoriteButtonProps {
  skillId: number
  size?: 'small' | 'middle' | 'large'
  showText?: boolean
  onFavoriteChange?: (isFavorited: boolean) => void
}

export default function FavoriteButton({
  skillId,
  size = 'middle',
  showText = true,
  onFavoriteChange,
}: FavoriteButtonProps) {
  const { isFavorited, toggle, isLoading } = useToggleFavorite(skillId)

  const handleClick = async () => {
    try {
      await toggle()
      message.success(isFavorited ? '已取消收藏' : '收藏成功')
      onFavoriteChange?.(!isFavorited)
    } catch (error) {
      message.error('操作失败，请重试')
    }
  }

  return (
    <Tooltip title={isFavorited ? '取消收藏' : '收藏'}>
      <Button
        type={isFavorited ? 'primary' : 'default'}
        icon={isFavorited ? <StarFilled /> : <StarOutlined />}
        size={size}
        onClick={handleClick}
        loading={isLoading}
        className={`favorite-button ${isFavorited ? 'favorited' : ''}`}
      >
        {showText && (isFavorited ? '已收藏' : '收藏')}
      </Button>
    </Tooltip>
  )
}
