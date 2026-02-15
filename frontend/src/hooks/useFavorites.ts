import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { favoritesApi } from '@/api/favorites'

// 获取收藏列表
export function useFavorites(page?: number, pageSize?: number) {
  return useQuery({
    queryKey: ['favorites', page, pageSize],
    queryFn: () => favoritesApi.getFavorites({ page, page_size: pageSize }),
  })
}

// 检查是否已收藏
export function useIsFavorited(skillId: number) {
  return useQuery({
    queryKey: ['favorites', skillId, 'check'],
    queryFn: () => favoritesApi.checkFavorite(skillId),
    enabled: !!skillId,
  })
}

// 添加收藏
export function useAddFavorite() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (skillId: number) => favoritesApi.addFavorite(skillId),
    onSuccess: (_, skillId) => {
      // 刷新收藏状态和列表
      queryClient.invalidateQueries({ queryKey: ['favorites', skillId, 'check'] })
      queryClient.invalidateQueries({ queryKey: ['favorites'] })
    },
  })
}

// 取消收藏
export function useRemoveFavorite() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (skillId: number) => favoritesApi.removeFavorite(skillId),
    onSuccess: (_, skillId) => {
      // 刷新收藏状态和列表
      queryClient.invalidateQueries({ queryKey: ['favorites', skillId, 'check'] })
      queryClient.invalidateQueries({ queryKey: ['favorites'] })
    },
  })
}

// 收藏/取消收藏切换
export function useToggleFavorite(skillId: number) {
  const { data: isFavorited } = useIsFavorited(skillId)
  const addFavorite = useAddFavorite()
  const removeFavorite = useRemoveFavorite()
  
  const toggle = () => {
    if (isFavorited) {
      removeFavorite.mutate(skillId)
    } else {
      addFavorite.mutate(skillId)
    }
  }
  
  return {
    isFavorited,
    toggle,
    isLoading: addFavorite.isPending || removeFavorite.isPending,
  }
}
