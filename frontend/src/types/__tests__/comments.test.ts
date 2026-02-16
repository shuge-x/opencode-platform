// Types tests - verifying type exports
import {
  Comment,
  CreateCommentRequest,
  UpdateCommentRequest,
  CommentListResponse,
} from '../comments'

describe('Comment Types', () => {
  it('should have Comment type', () => {
    const comment: Comment = {
      id: 1,
      user_id: 1,
      skill_id: 1,
      content: 'Great skill!',
      likes_count: 5,
      is_edited: false,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      user: {
        id: 1,
        username: 'testuser',
      },
    }
    
    expect(comment.id).toBe(1)
    expect(comment.content).toBe('Great skill!')
  })

  it('should have CreateCommentRequest type', () => {
    const request: CreateCommentRequest = {
      skill_id: 1,
      content: 'New comment',
      parent_id: undefined,
    }
    
    expect(request.skill_id).toBe(1)
    expect(request.content).toBe('New comment')
  })

  it('should have UpdateCommentRequest type', () => {
    const request: UpdateCommentRequest = {
      content: 'Updated comment',
    }
    
    expect(request.content).toBe('Updated comment')
  })

  it('should have CommentListResponse type', () => {
    const response: CommentListResponse = {
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
      has_more: false,
    }
    
    expect(response.items).toEqual([])
    expect(response.total).toBe(0)
  })
})
