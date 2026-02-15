import client from './client'
import type { Favorite, FavoriteListResponse } from '@/types/comments'

export const favoritesApi = {
  // 获取收藏列表
  getFavorites: async (params?: { page?: number; page_size?: number }): Promise<FavoriteListResponse> => {
    const response = await client.get('/favorites', { 
      params: {
        page: params?.page || 1,
        page_size: params?.page_size || 20,
      }
    })
    return response.data
  },

  // 添加收藏
  addFavorite: async (skillId: number): Promise<Favorite> => {
    const response = await client.post(`/favorites`, { skill_id: skillId })
    return response.data
  },

  // 取消收藏
  removeFavorite: async (skillId: number): Promise<void> => {
    await client.delete(`/favorites/${skillId}`)
  },

  // 检查是否已收藏
  checkFavorite: async (skillId: number): Promise<boolean> => {
    try {
      const response = await client.get(`/favorites/check/${skillId}`)
      return response.data.is_favorited
    } catch (error: any) {
      if (error.response?.status === 404) {
        return false
      }
      throw error
    }
  },

  // 获取收藏数量
  getFavoriteCount: async (skillId: number): Promise<number> => {
    const response = await client.get(`/favorites/count/${skillId}`)
    return response.data.count
  },
}
