// 评论相关类型定义
export interface Comment {
  id: number
  skill_id: number
  user_id: number
  parent_id?: number
  content: string
  rating?: number
  likes_count: number
  is_edited: boolean
  created_at: string
  updated_at: string
  user?: CommentUser
  replies?: Comment[]
}

export interface CommentUser {
  id: number
  username: string
  avatar_url?: string
}

export interface CreateCommentRequest {
  skill_id: number
  content: string
  rating?: number
  parent_id?: number
}

export interface UpdateCommentRequest {
  content: string
  rating?: number
}

export interface CommentListParams {
  skill_id: number
  page?: number
  page_size?: number
  sort_by?: 'latest' | 'popular'
  parent_id?: number
}

export interface CommentListResponse {
  items: Comment[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

// 评分相关类型
export interface SkillRating {
  skill_id: number
  average_rating: number
  rating_count: number
  rating_distribution: RatingDistribution
}

export interface RatingDistribution {
  five_star: number
  four_star: number
  three_star: number
  two_star: number
  one_star: number
}

export interface UserRating {
  skill_id: number
  rating: number
  created_at: string
  updated_at: string
}

export interface CreateRatingRequest {
  skill_id: number
  rating: number
}

// 收藏相关类型
export interface Favorite {
  id: number
  skill_id: number
  user_id: number
  created_at: string
  skill?: {
    id: number
    name: string
    description?: string
    version: string
    rating: string
    download_count: number
  }
}

export interface FavoriteListResponse {
  items: Favorite[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}
