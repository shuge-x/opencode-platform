import client from './client'
import type { 
  SkillRating, 
  UserRating, 
  CreateRatingRequest,
  RatingDistribution 
} from '@/types/comments'

export const ratingsApi = {
  // 获取技能评分统计
  getSkillRating: async (skillId: number): Promise<SkillRating> => {
    const response = await client.get(`/skills/${skillId}/rating`)
    return response.data
  },

  // 获取评分分布
  getRatingDistribution: async (skillId: number): Promise<RatingDistribution> => {
    const response = await client.get(`/skills/${skillId}/rating/distribution`)
    return response.data
  },

  // 获取用户对技能的评分
  getUserRating: async (skillId: number): Promise<UserRating | null> => {
    try {
      const response = await client.get(`/skills/${skillId}/rating/user`)
      return response.data
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null
      }
      throw error
    }
  },

  // 创建或更新评分
  createOrUpdateRating: async (data: CreateRatingRequest): Promise<UserRating> => {
    const response = await client.post(`/skills/${data.skill_id}/rating`, { rating: data.rating })
    return response.data
  },

  // 删除评分
  deleteRating: async (skillId: number): Promise<void> => {
    await client.delete(`/skills/${skillId}/rating`)
  },
}
