import React, { useState } from 'react'
import { 
  List, 
  Avatar, 
  Button, 
  Form, 
  Input, 
  Rate, 
  Space, 
  Typography, 
  Dropdown,
  Modal,
  message,
  Empty,
  Spin,
  Pagination,
  Radio,
  Tooltip
} from 'antd'
import { 
  LikeOutlined, 
  LikeFilled, 
  EditOutlined, 
  DeleteOutlined, 
  MoreOutlined,
  ReplyOutlined,
  UserOutlined,
  ClockCircleOutlined
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import type { Comment } from '@/types/comments'
import { 
  useComments, 
  useCreateComment, 
  useUpdateComment, 
  useDeleteComment,
  useLikeComment 
} from '@/hooks/useComments'
import './CommentSection.css'

const { Text, Paragraph } = Typography
const { TextArea } = Input

interface CommentSectionProps {
  skillId: number
  currentUserId?: number
}

export default function CommentSection({ skillId, currentUserId }: CommentSectionProps) {
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState<'latest' | 'popular'>('latest')
  const [replyTo, setReplyTo] = useState<Comment | null>(null)
  const [editingComment, setEditingComment] = useState<Comment | null>(null)
  const [deleteModal, setDeleteModal] = useState<{ visible: boolean; commentId?: number }>({
    visible: false
  })
  
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()

  const { data, isLoading, refetch } = useComments({
    skill_id: skillId,
    page,
    page_size: 10,
    sort_by: sortBy,
  })

  const createComment = useCreateComment()
  const updateComment = useUpdateComment()
  const deleteComment = useDeleteComment()
  const likeComment = useLikeComment()

  // 提交评论
  const handleSubmit = async (values: { content: string; rating?: number }) => {
    try {
      await createComment.mutateAsync({
        skill_id: skillId,
        content: values.content,
        rating: values.rating,
        parent_id: replyTo?.id,
      })
      form.resetFields()
      setReplyTo(null)
      message.success('评论发布成功')
      refetch()
    } catch (error) {
      message.error('评论发布失败')
    }
  }

  // 更新评论
  const handleUpdate = async (values: { content: string; rating?: number }) => {
    if (!editingComment) return
    
    try {
      await updateComment.mutateAsync({
        commentId: editingComment.id,
        data: values,
      })
      editForm.resetFields()
      setEditingComment(null)
      message.success('评论更新成功')
    } catch (error) {
      message.error('评论更新失败')
    }
  }

  // 删除评论
  const handleDelete = async () => {
    if (!deleteModal.commentId) return
    
    try {
      await deleteComment.mutateAsync(deleteModal.commentId)
      setDeleteModal({ visible: false })
      message.success('评论删除成功')
    } catch (error) {
      message.error('评论删除失败')
    }
  }

  // 点赞
  const handleLike = (comment: Comment) => {
    // 这里简化处理，实际应该检查用户是否已点赞
    likeComment.mutate({ commentId: comment.id, like: true })
  }

  // 获取评论操作菜单
  const getCommentMenu = (comment: Comment): MenuProps['items'] => {
    const isOwner = currentUserId === comment.user_id
    const items: MenuProps['items'] = [
      {
        key: 'reply',
        icon: <ReplyOutlined />,
        label: '回复',
        onClick: () => setReplyTo(comment),
      },
    ]

    if (isOwner) {
      items.push(
        {
          key: 'edit',
          icon: <EditOutlined />,
          label: '编辑',
          onClick: () => {
            setEditingComment(comment)
            editForm.setFieldsValue({
              content: comment.content,
              rating: comment.rating,
            })
          },
        },
        {
          key: 'delete',
          icon: <DeleteOutlined />,
          label: '删除',
          danger: true,
          onClick: () => setDeleteModal({ visible: true, commentId: comment.id }),
        }
      )
    }

    return items
  }

  // 渲染单个评论
  const renderComment = (comment: Comment) => {
    const isOwner = currentUserId === comment.user_id

    return (
      <div className="comment-item">
        <div className="comment-avatar">
          <Avatar 
            src={comment.user?.avatar_url} 
            icon={<UserOutlined />}
            size={40}
          />
        </div>
        
        <div className="comment-content">
          <div className="comment-header">
            <Space>
              <Text strong>{comment.user?.username || `用户${comment.user_id}`}</Text>
              {comment.rating && (
                <Rate disabled value={comment.rating} className="comment-rating" />
              )}
            </Space>
            <Text type="secondary" className="comment-time">
              <ClockCircleOutlined /> {new Date(comment.created_at).toLocaleString('zh-CN')}
              {comment.is_edited && <Text type="secondary"> (已编辑)</Text>}
            </Text>
          </div>
          
          <Paragraph className="comment-text">{comment.content}</Paragraph>
          
          <div className="comment-actions">
            <Space>
              <Tooltip title="点赞">
                <Button 
                  type="text" 
                  size="small"
                  icon={<LikeOutlined />}
                  onClick={() => handleLike(comment)}
                >
                  {comment.likes_count || 0}
                </Button>
              </Tooltip>
              
              <Button 
                type="text" 
                size="small"
                icon={<ReplyOutlined />}
                onClick={() => setReplyTo(comment)}
              >
                回复
              </Button>
            </Space>
            
            <Dropdown menu={{ items: getCommentMenu(comment) }} trigger={['click']}>
              <Button type="text" size="small" icon={<MoreOutlined />} />
            </Dropdown>
          </div>

          {/* 回复列表 */}
          {comment.replies && comment.replies.length > 0 && (
            <div className="replies-list">
              {comment.replies.map((reply) => renderComment(reply))}
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="comment-section">
      {/* 排序选项 */}
      <div className="comment-header-bar">
        <Text strong>全部评论 ({data?.total || 0})</Text>
        <Radio.Group 
          value={sortBy} 
          onChange={(e) => {
            setSortBy(e.target.value)
            setPage(1)
          }}
          size="small"
        >
          <Radio.Button value="latest">最新</Radio.Button>
          <Radio.Button value="popular">最热</Radio.Button>
        </Radio.Group>
      </div>

      {/* 发表评论表单 */}
      <div className="comment-form">
        {replyTo && (
          <div className="reply-to-bar">
            <Text type="secondary">
              回复 <Text strong>@{replyTo.user?.username || `用户${replyTo.user_id}`}</Text>
            </Text>
            <Button 
              type="text" 
              size="small" 
              onClick={() => setReplyTo(null)}
            >
              取消
            </Button>
          </div>
        )}
        
        <Form form={form} onFinish={handleSubmit} layout="vertical">
          {!replyTo && (
            <Form.Item name="rating" label="评分">
              <Rate allowClear />
            </Form.Item>
          )}
          
          <Form.Item 
            name="content" 
            rules={[{ required: true, message: '请输入评论内容' }]}
          >
            <TextArea 
              rows={4} 
              placeholder={replyTo ? '写下你的回复...' : '写下你的评论...'}
              maxLength={1000}
              showCount
            />
          </Form.Item>
          
          <Form.Item style={{ marginBottom: 0 }}>
            <Button 
              type="primary" 
              htmlType="submit"
              loading={createComment.isPending}
            >
              {replyTo ? '发表回复' : '发表评论'}
            </Button>
          </Form.Item>
        </Form>
      </div>

      {/* 评论列表 */}
      <Spin spinning={isLoading}>
        {data?.items && data.items.length > 0 ? (
          <>
            <List
              dataSource={data.items}
              renderItem={renderComment}
              className="comment-list"
            />
            
            {data.has_more && (
              <div className="pagination-wrapper">
                <Pagination
                  current={page}
                  pageSize={data.page_size}
                  total={data.total}
                  onChange={(p) => setPage(p)}
                  showSizeChanger={false}
                  showTotal={(total) => `共 ${total} 条评论`}
                />
              </div>
            )}
          </>
        ) : (
          <Empty description="暂无评论，快来发表第一条评论吧！" />
        )}
      </Spin>

      {/* 编辑评论模态框 */}
      <Modal
        title="编辑评论"
        open={!!editingComment}
        onCancel={() => {
          setEditingComment(null)
          editForm.resetFields()
        }}
        footer={null}
      >
        <Form form={editForm} onFinish={handleUpdate} layout="vertical">
          {editingComment && !editingComment.parent_id && (
            <Form.Item name="rating" label="评分">
              <Rate allowClear />
            </Form.Item>
          )}
          
          <Form.Item 
            name="content" 
            rules={[{ required: true, message: '请输入评论内容' }]}
          >
            <TextArea rows={4} maxLength={1000} showCount />
          </Form.Item>
          
          <Form.Item style={{ marginBottom: 0 }}>
            <Space>
              <Button 
                type="primary" 
                htmlType="submit"
                loading={updateComment.isPending}
              >
                保存
              </Button>
              <Button onClick={() => {
                setEditingComment(null)
                editForm.resetFields()
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 删除确认模态框 */}
      <Modal
        title="确认删除"
        open={deleteModal.visible}
        onOk={handleDelete}
        onCancel={() => setDeleteModal({ visible: false })}
        confirmLoading={deleteComment.isPending}
        okText="删除"
        cancelText="取消"
        okButtonProps={{ danger: true }}
      >
        <Text>确定要删除这条评论吗？此操作不可恢复。</Text>
      </Modal>
    </div>
  )
}
