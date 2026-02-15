import client from './client'
import type { 
  Comment, 
  CreateCommentRequest, 
  UpdateCommentRequest, 
  CommentListParams,
  CommentListResponse 
} from '@/types/comments'

export const commentsApi = {
  // 获取评论列表
  getComments: async (params: CommentListParams): Promise<CommentListResponse> => {
    const queryParams: Record<string, any> = {
      skill_id: params.skill_id,
      page: params.page || 1,
      page_size: params.page_size || 10,
    }
    
    if (params.sort_by) {
      queryParams.sort_by = params.sort_by
    }
    
    if (params.parent_id) {
      queryParams.parent_id = params.parent_id
    }
    
    const response = await client.get('/comments', { params: queryParams })
    return response.data
  },

  // 获取单条评论
  getComment: async (commentId: number): Promise<Comment> => {
    const response = await client.get(`/comments/${commentId}`)
    return response.data
  },

  // 创建评论
  createComment: async (data: CreateCommentRequest): Promise<Comment> => {
    const response = await client.post('/comments', data)
    return response.data
  },

  // 更新评论
  updateComment: async (commentId: number, data: UpdateCommentRequest): Promise<Comment> => {
    const response = await client.put(`/comments/${commentId}`, data)
    return response.data
  },

  // 删除评论
  deleteComment: async (commentId: number): Promise<void> => {
    await client.delete(`/comments/${commentId}`)
  },

  // 点赞评论
  likeComment: async (commentId: number): Promise<void> => {
    await client.post(`/comments/${commentId}/like`)
  },

  // 取消点赞
  unlikeComment: async (commentId: number): Promise<void> => {
    await client.delete(`/comments/${commentId}/like`)
  },

  // 获取评论的回复列表
  getReplies: async (commentId: number, params?: { page?: number; page_size?: number }): Promise<CommentListResponse> => {
    const response = await client.get(`/comments/${commentId}/replies`, { params })
    return response.data
  },
}
