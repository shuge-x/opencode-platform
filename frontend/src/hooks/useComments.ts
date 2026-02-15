import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { commentsApi } from '@/api/comments'
import type { CommentListParams, CreateCommentRequest, UpdateCommentRequest } from '@/types/comments'

// 获取评论列表
export function useComments(params: CommentListParams) {
  return useQuery({
    queryKey: ['comments', params],
    queryFn: () => commentsApi.getComments(params),
    enabled: !!params.skill_id,
  })
}

// 创建评论
export function useCreateComment() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: CreateCommentRequest) => commentsApi.createComment(data),
    onSuccess: (_, variables) => {
      // 刷新评论列表
      queryClient.invalidateQueries({ 
        queryKey: ['comments', { skill_id: variables.skill_id }] 
      })
    },
  })
}

// 更新评论
export function useUpdateComment() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ commentId, data }: { commentId: number; data: UpdateCommentRequest }) => 
      commentsApi.updateComment(commentId, data),
    onSuccess: () => {
      // 刷新所有评论列表
      queryClient.invalidateQueries({ queryKey: ['comments'] })
    },
  })
}

// 删除评论
export function useDeleteComment() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (commentId: number) => commentsApi.deleteComment(commentId),
    onSuccess: () => {
      // 刷新所有评论列表
      queryClient.invalidateQueries({ queryKey: ['comments'] })
    },
  })
}

// 点赞/取消点赞
export function useLikeComment() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ commentId, like }: { commentId: number; like: boolean }) => 
      like ? commentsApi.likeComment(commentId) : commentsApi.unlikeComment(commentId),
    onSuccess: () => {
      // 刷新评论列表以更新点赞数
      queryClient.invalidateQueries({ queryKey: ['comments'] })
    },
  })
}

// 获取回复列表
export function useReplies(commentId: number, page?: number) {
  return useQuery({
    queryKey: ['comments', commentId, 'replies', page],
    queryFn: () => commentsApi.getReplies(commentId, { page, page_size: 5 }),
    enabled: !!commentId,
  })
}
