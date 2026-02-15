import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ratingsApi } from '@/api/ratings'
import type { CreateRatingRequest } from '@/types/comments'

// 获取技能评分统计
export function useSkillRating(skillId: number) {
  return useQuery({
    queryKey: ['rating', skillId],
    queryFn: () => ratingsApi.getSkillRating(skillId),
    enabled: !!skillId,
  })
}

// 获取用户评分
export function useUserRating(skillId: number) {
  return useQuery({
    queryKey: ['rating', skillId, 'user'],
    queryFn: () => ratingsApi.getUserRating(skillId),
    enabled: !!skillId,
  })
}

// 创建或更新评分
export function useCreateOrUpdateRating() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: CreateRatingRequest) => ratingsApi.createOrUpdateRating(data),
    onSuccess: (_, variables) => {
      // 刷新评分统计和用户评分
      queryClient.invalidateQueries({ queryKey: ['rating', variables.skill_id] })
    },
  })
}

// 删除评分
export function useDeleteRating() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (skillId: number) => ratingsApi.deleteRating(skillId),
    onSuccess: (skillId) => {
      // 刷新评分相关数据
      queryClient.invalidateQueries({ queryKey: ['rating', skillId] })
    },
  })
}
